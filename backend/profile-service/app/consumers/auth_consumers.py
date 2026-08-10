import uuid
from typing import Dict, Any

from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.services.profile_service import ProfileService
from app.database.session import async_session_factory
from app.core.config import settings
from app.core.logger import logger

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления пользователя из auth-service"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by profile-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in user deletion event")
            return False
        
        logger.info(f"Processing user deletion for {keycloak_id}")
        
        # ИСПРАВЛЕНО: Создаем ProfileService без передачи session
        from app.services.keycloak_client import KeycloakClient
        kc_client = KeycloakClient()
        profile_service = ProfileService(kc_client)  # <- Убран session
        
        # Удаляем профили пользователя
        success = await profile_service.delete_profiles_by_keycloak_id(keycloak_id)
        
        if success:
            logger.info(f"Profiles deleted for user {keycloak_id}")
        else:
            logger.warning(f"No profiles found for user {keycloak_id} or deletion failed")
        
        return True
            
    except Exception as e:
        logger.error(f"Error handling user deletion: {e}", exc_info=True)
        return False

async def register(consumer):
    """Регистрация consumers для событий от auth-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETED,
            callback=handle_user_deleted
        )
        
        logger.info("Auth event consumers registered successfully in profile-service")
    except Exception as e:
        logger.error(f"Failed to register auth consumers: {e}", exc_info=True)
        raise