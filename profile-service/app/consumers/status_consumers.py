from datetime import datetime
from typing import Dict, Any

from shared.events.schemas import EventType, BaseEvent
from app.services.rabbitmq import rabbitmq_consumer
from app.services.profile_service import ProfileService
from app.database.session import async_session_factory
from app.core.config import settings
from app.core.logger import logger
from app.services.keycloak_client import KeycloakClient

async def handle_user_online(event: Dict[str, Any]) -> bool:
    """Обработка события USER_ONLINE"""
    try:
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by profile-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in USER_ONLINE event")
            return False
        
        logger.info(f"Processing USER_ONLINE for {keycloak_id}")
        
        # Обновляем статус в БД
        kc_client = KeycloakClient()
        profile_service = ProfileService(kc_client)
        
        success = await profile_service.update_online_status(keycloak_id, online=True)
        
        if success:
            logger.info(f"User {keycloak_id} marked as ONLINE")
        else:
            logger.warning(f"Failed to mark {keycloak_id} as ONLINE (profile not found?)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling USER_ONLINE event: {e}", exc_info=True)
        return False

async def handle_user_offline(event: Dict[str, Any]) -> bool:
    """Обработка события USER_OFFLINE"""
    try:
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by profile-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        reason = user_data.get("reason", "unknown")
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in USER_OFFLINE event")
            return False
        
        logger.info(f"Processing USER_OFFLINE for {keycloak_id} (reason: {reason})")
        
        # Обновляем статус в БД
        kc_client = KeycloakClient()
        profile_service = ProfileService(kc_client)
        
        success = await profile_service.update_online_status(keycloak_id, online=False)
        
        if success:
            logger.info(f"User {keycloak_id} marked as OFFLINE")
        else:
            logger.warning(f"Failed to mark {keycloak_id} as OFFLINE")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling USER_OFFLINE event: {e}", exc_info=True)
        return False

async def register(consumer):
    """Регистрация consumers для событий статуса"""
    try:
        # Подписка на USER_ONLINE
        await consumer.consume_user_events(
            event_type=EventType.USER_ONLINE,
            callback=handle_user_online
        )
        
        # Подписка на USER_OFFLINE
        await consumer.consume_user_events(
            event_type=EventType.USER_OFFLINE,
            callback=handle_user_offline
        )
        
        logger.info("Status event consumers registered successfully in profile-service")
    except Exception as e:
        logger.error(f"Failed to register status consumers: {e}", exc_info=True)
        raise