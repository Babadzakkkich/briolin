import json
from typing import Dict, Any
from app.services.rabbitmq import rabbitmq_consumer
from app.services.user_service import UserService
from app.database.session import async_session_factory
from shared.schemas.shared import UserRole
from app.schemas.internal import UserProfileCreate
from app.core.logger import logger

async def handle_user_registered(event: Dict[str, Any]) -> bool:
    """Обработка события регистрации пользователя из auth-service"""
    try:
        user_data = event.get("user_data", {})
        source_service = event.get("source_service", "")
        
        logger.debug(f"Processing user registration event from {source_service}: {user_data}")
        
        required_fields = ["keycloak_id", "email", "username", "first_name", "last_name", "role"]
        for field in required_fields:
            if field not in user_data:
                logger.error(f"Missing required field {field} in user registration event")
                logger.error(f"Event data: {event}")
                return False
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Создаем профиль пользователя
            profile_data = UserProfileCreate(
                keycloak_id=user_data["keycloak_id"],
                email=user_data["email"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=UserRole(user_data["role"])
            )
            
            user = await user_service.create_user_profile(profile_data)
            
            if user:
                logger.info(f"Created user profile for: {user_data['username']} from {source_service}")
                return True
            else:
                logger.error(f"Failed to create user profile for: {user_data['username']}")
                return False
                
    except Exception as e:
        logger.error(f"Error handling user registration event: {e}", exc_info=True)
        return False

async def handle_user_updated(event: Dict[str, Any]) -> bool:
    """Обработка события обновления пользователя из auth-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        source_service = event.get("source_service", "")
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user update event")
            return False
        
        logger.debug(f"Processing user update event from {source_service} for {keycloak_id}: {updated_fields}")
        
        # Фильтруем поля, которые можно обновить в user-service
        allowed_fields = ["email", "first_name", "last_name", "username"]
        user_update_fields = {
            k: v for k, v in updated_fields.items() 
            if k in allowed_fields and v is not None
        }
        
        if not user_update_fields:
            logger.debug(f"No relevant fields to update in user-service for {keycloak_id}")
            return True
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Получаем пользователя по keycloak_id
            user = await user_service.get_user_by_keycloak_id(keycloak_id)
            if not user:
                logger.warning(f"User {keycloak_id} not found in user-service")
                return False
            
            # Обновляем поля
            old_values = {}
            for field, value in user_update_fields.items():
                old_values[field] = getattr(user, field)
                setattr(user, field, value)
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Updated user {keycloak_id} from {source_service}: {user_update_fields}")
            return True
            
    except Exception as e:
        logger.error(f"Error handling user update event: {e}")
        return False

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления пользователя из auth-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        source_service = event.get("source_service", "")
        
        # ИГНОРИРУЕМ события от user-service (чтобы избежать цикл)
        if source_service == "user-service":
            logger.debug(f"Ignoring deletion event from user-service for {keycloak_id}")
            return True
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion event")
            return False
        
        logger.debug(f"Processing user deletion event from auth-service for {keycloak_id}")
        
        # Уже обработано в основном потоке удаления
        # Просто логируем подтверждение
        logger.info(f"User deletion confirmed by auth-service for {keycloak_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling user deletion event: {e}")
        return False

async def register(consumer):
    """Регистрация consumers для событий от auth-service"""
    try:
        # Подписка на регистрацию пользователей
        await consumer.consume_user_events(
            event_type="registered",
            callback=handle_user_registered
        )
        
        # Подписка на обновления пользователей
        await consumer.consume_user_events(
            event_type="updated",
            callback=handle_user_updated
        )
        
        # Подписка на удаление пользователей
        await consumer.consume_user_events(
            event_type="deleted",
            callback=handle_user_deleted
        )
        
        logger.info("Auth event consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register auth consumers: {e}", exc_info=True)
        raise