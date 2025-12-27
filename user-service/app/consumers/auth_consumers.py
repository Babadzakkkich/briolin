from datetime import datetime
import json
from typing import Dict, Any

from sqlalchemy import delete
from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.services.user_service import UserService
from app.database.session import async_session_factory
from app.database.models import UserRoleAssignment
from shared.schemas.shared import UserRole
from app.schemas.internal import UserProfileCreate
from app.core.config import settings
from app.core.logger import logger
from app.services.event_waiter import get_event_waiter

async def handle_user_registered(event: Dict[str, Any]) -> bool:
    """Обработка события регистрации пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        source_service = base_event.source_service
        correlation_id = base_event.correlation_id
        
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
                
                # Если кто-то ожидает это событие, уведомляем
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "success",
                    "user_id": user.id,
                    "keycloak_id": user.keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                logger.error(f"Failed to create user profile for: {user_data['username']}")
                return False
                
    except Exception as e:
        logger.error(f"Error handling user registration event: {e}", exc_info=True)
        return False

async def handle_user_profile_updated(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения обновления профиля пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        from datetime import datetime
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        correlation_id = base_event.correlation_id
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user profile update confirmation")
            return False
        
        logger.info(f"Processing profile update confirmation for {keycloak_id} (correlation: {correlation_id})")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Обновляем в локальной БД user-service
            success = await user_service.update_user_from_event(
                keycloak_id=keycloak_id,
                updated_fields=updated_fields,
                source_service=source_service
            )
            
            if success:
                logger.info(f"User {keycloak_id} updated locally from auth-service confirmation")
                
                # Уведомляем ожидающих это событие
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "success",
                    "keycloak_id": keycloak_id,
                    "updated_fields": updated_fields,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source_service": source_service
                })
                
            else:
                logger.warning(f"Failed to update user {keycloak_id} locally")
                
                # Уведомляем об ошибке
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "error",
                    "error": "Failed to update user locally",
                    "keycloak_id": keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user profile update confirmation: {e}")
        
        # Уведомляем об ошибке
        event_waiter = get_event_waiter()
        correlation_id = base_event.correlation_id
        await event_waiter.set_event_result(correlation_id, {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return False

async def handle_user_status_changed(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения изменения статуса пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        from datetime import datetime
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_active = user_data.get("is_active")
        correlation_id = base_event.correlation_id
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id or is_active is None:
            logger.error("Missing keycloak_id or is_active in user status change confirmation")
            return False
        
        logger.info(f"Processing status change confirmation for {keycloak_id} (correlation: {correlation_id})")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Обновляем статус в локальной БД user-service
            success = await user_service.update_user_from_event(
                keycloak_id=keycloak_id,
                updated_fields={"is_active": is_active},
                source_service=source_service
            )
            
            if success:
                logger.info(f"User {keycloak_id} status updated locally to {is_active}")
                
                # Уведомляем ожидающих
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "success",
                    "keycloak_id": keycloak_id,
                    "is_active": is_active,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source_service": source_service
                })
                
            else:
                logger.warning(f"Failed to update user status {keycloak_id} locally")
                
                # Уведомляем об ошибке
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "error",
                    "error": "Failed to update user status locally",
                    "keycloak_id": keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user status change confirmation: {e}")
        return False

async def handle_user_roles_updated(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения обновления ролей пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        from datetime import datetime
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        roles = user_data.get("roles", [])
        correlation_id = base_event.correlation_id
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user roles update confirmation")
            return False
        
        logger.info(f"Processing roles update confirmation for {keycloak_id} (correlation: {correlation_id})")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Находим пользователя
            user = await user_service.get_user_by_keycloak_id(keycloak_id)
            if not user:
                logger.warning(f"User {keycloak_id} not found in user-service")
                
                # Уведомляем об ошибке
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "error",
                    "error": f"User {keycloak_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return False
            
            # Преобразуем строки ролей в enum
            role_enums = [UserRole(role) for role in roles if role in UserRole._value2member_map_]
            
            # Удаляем старые роли
            await session.execute(
                delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user.id)
            )
            
            # Добавляем новые роли
            for role_enum in role_enums:
                role_assignment = UserRoleAssignment(
                    user_id=user.id,
                    role=role_enum
                )
                session.add(role_assignment)
            
            try:
                await session.commit()
                logger.info(f"User {keycloak_id} roles updated locally to {roles}")
                
                # Уведомляем ожидающих
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "success",
                    "keycloak_id": keycloak_id,
                    "roles": roles,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source_service": source_service
                })
                
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user roles locally: {e}")
                
                # Уведомляем об ошибке
                event_waiter = get_event_waiter()
                await event_waiter.set_event_result(correlation_id, {
                    "status": "error",
                    "error": str(e),
                    "keycloak_id": keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return False
            
    except Exception as e:
        logger.error(f"Error handling user roles update confirmation: {e}")
        return False

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения удаления пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        from datetime import datetime
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        correlation_id = base_event.correlation_id
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion confirmation")
            return False
        
        logger.info(f"Processing deletion confirmation for {keycloak_id} (correlation: {correlation_id})")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Находим пользователя
            user = await user_service.get_user_by_keycloak_id(keycloak_id)
            
            deletion_performed = False
            deletion_success = False
            
            if user:
                # Удаляем пользователя из локальной БД
                try:
                    # Используем session.delete() напрямую, чтобы избежать конфликтов с ORM
                    await session.delete(user)
                    await session.commit()
                    deletion_performed = True
                    deletion_success = True
                    logger.info(f"User {keycloak_id} deleted locally from auth-service confirmation")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to delete user locally: {e}")
                    deletion_performed = True
                    deletion_success = False
            else:
                logger.warning(f"User {keycloak_id} not found in user-service (already deleted?)")
                deletion_performed = False
                deletion_success = True  # Считаем успехом, если уже удален
            
            # Уведомляем ожидающих
            event_waiter = get_event_waiter()
            
            if deletion_success:
                await event_waiter.set_event_result(correlation_id, {
                    "status": "success",
                    "keycloak_id": keycloak_id,
                    "deletion_performed": deletion_performed,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source_service": source_service
                })
            else:
                await event_waiter.set_event_result(correlation_id, {
                    "status": "error",
                    "error": "Failed to delete user locally" if deletion_performed else "User not found",
                    "keycloak_id": keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return deletion_success
            
    except Exception as e:
        logger.error(f"Error handling user deletion confirmation: {e}", exc_info=True)
        
        # Уведомляем об ошибке
        event_waiter = get_event_waiter()
        correlation_id = base_event.correlation_id
        await event_waiter.set_event_result(correlation_id, {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return False

async def register(consumer):
    """Регистрация consumers для событий от auth-service"""
    try:
        # Регистрируем обработчики для событий регистрации
        await consumer.consume_user_events(
            event_type=EventType.USER_REGISTERED,
            callback=handle_user_registered
        )
        
        # Регистрируем обработчики для CONFIRMATION событий от auth-service
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_UPDATED,
            callback=handle_user_profile_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_STATUS_CHANGED,
            callback=handle_user_status_changed
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_ROLES_UPDATED,
            callback=handle_user_roles_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETED,
            callback=handle_user_deleted
        )
        
        logger.info("Auth event consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register auth consumers: {e}", exc_info=True)
        raise