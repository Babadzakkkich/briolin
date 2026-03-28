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
from app.services.saga_worker import get_saga_worker


async def handle_user_profile_updated(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения обновления профиля пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        
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
        
        logger.info(f"Processing profile update confirmation for {keycloak_id}")
        
        # Просто обновляем локальную БД через update_user_from_event
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            success = await user_service.update_user_from_event(
                keycloak_id=keycloak_id,
                updated_fields=updated_fields,
                source_service=source_service
            )
            
            if success:
                logger.info(f"User {keycloak_id} updated locally from auth-service confirmation")
            else:
                logger.warning(f"Failed to update user {keycloak_id} locally")
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user profile update confirmation: {e}")
        return False


async def handle_user_status_changed(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения изменения статуса пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_active = user_data.get("is_active")
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id or is_active is None:
            logger.error("Missing keycloak_id or is_active in user status change confirmation")
            return False
        
        logger.info(f"Processing status change confirmation for {keycloak_id}: {is_active}")
        
        # Обновляем статус в локальной БД
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            success = await user_service.update_user_from_event(
                keycloak_id=keycloak_id,
                updated_fields={"is_active": is_active},
                source_service=source_service
            )
            
            if success:
                logger.info(f"User {keycloak_id} status updated locally to {is_active}")
            else:
                logger.warning(f"Failed to update user status {keycloak_id} locally")
            
            return success
            
    except Exception as e:
        logger.error(f"Error handling user status change confirmation: {e}")
        return False


async def handle_user_roles_updated(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения обновления ролей пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        roles = user_data.get("roles", [])
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user roles update confirmation")
            return False
        
        logger.info(f"Processing roles update confirmation for {keycloak_id}: {roles}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Находим пользователя
            user = await user_service.get_user_by_keycloak_id(keycloak_id)
            if not user:
                logger.warning(f"User {keycloak_id} not found in user-service")
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
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user roles locally: {e}")
                return False
            
    except Exception as e:
        logger.error(f"Error handling user roles update confirmation: {e}")
        return False


async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события подтверждения удаления пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        source_service = user_data.get("source_service", base_event.source_service)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion confirmation")
            return False
        
        logger.info(f"Processing deletion confirmation for {keycloak_id}")
        
        async with async_session_factory() as session:
            from app.services.keycloak_client import KeycloakClient
            kc_client = KeycloakClient()
            user_service = UserService(session, kc_client)
            
            # Находим пользователя
            user = await user_service.get_user_by_keycloak_id(keycloak_id)
            
            if user:
                # Удаляем пользователя из локальной БД
                try:
                    await session.delete(user)
                    await session.commit()
                    logger.info(f"User {keycloak_id} deleted locally from auth-service confirmation")
                    return True
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to delete user locally: {e}")
                    return False
            else:
                logger.info(f"User {keycloak_id} not found in user-service (already deleted)")
                return True  # Считаем успехом, если уже удален
            
    except Exception as e:
        logger.error(f"Error handling user deletion confirmation: {e}", exc_info=True)
        return False


async def register(consumer):
    """Регистрация consumers для событий от auth-service"""
    try:
        # Удалена регистрация USER_REGISTERED
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