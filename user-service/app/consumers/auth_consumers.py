import json
from typing import Dict, Any
from shared.events.schemas import EventType
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
        processed_by = event.get("processed_by", [])
        
        logger.debug(f"Processing user registration event from {source_service}: {user_data}")
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "user-service" in processed_by:
            logger.debug(f"Event already processed by user-service")
            return True
        
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
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user update event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "user-service" in processed_by:
            logger.debug(f"Event already processed by user-service for {keycloak_id}")
            return True
        
        logger.debug(f"Processing user update event from auth-service for {keycloak_id}: {updated_fields}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Просто обновляем данные без дополнительных проверок
            success = await user_service.update_user_from_event(
                keycloak_id=keycloak_id,
                updated_fields=updated_fields,
                source_service="auth-service"
            )
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user update event: {e}")
        return False

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления пользователя из auth-service"""
    try:
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        source_service = event.get("source_service", "")
        processed_by = event.get("processed_by", [])
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion event")
            return False
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if "user-service" in processed_by:
            logger.debug(f"Event already processed by user-service for {keycloak_id}")
            return True
        
        logger.debug(f"Processing user deletion event from auth-service for {keycloak_id}")
        
        # Просто логируем подтверждение удаления
        logger.info(f"User deletion confirmed by auth-service for {keycloak_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling user deletion event: {e}")
        return False

async def register(consumer):
    """Регистрация consumers для событий от auth-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.USER_REGISTERED,
            callback=handle_user_registered
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_UPDATED,
            callback=handle_user_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETED,
            callback=handle_user_deleted
        )
        
        logger.info("Auth event consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register auth consumers: {e}", exc_info=True)
        raise