from shared.events.schemas import EventType, BaseEvent
from app.services.redis_cache import redis_cache
from app.core.config import settings
from app.core.logger import logger


async def handle_profile_updated(event: dict) -> bool:
    """Инвалидирует кэш эмбеддинга при обновлении профиля"""
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        
        # Проверяем, изменились ли поля, влияющие на эмбеддинг
        embedding_fields = {"about_me", "hobbies", "partner_preferences", "detailed_profile_created"}
        if not embedding_fields.intersection(updated_fields.keys()):
            return True
        
        if keycloak_id:
            await redis_cache.invalidate_user_cache(keycloak_id)
            logger.info(f"Invalidated embedding cache for {keycloak_id[:8]} due to profile update")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling profile update for cache invalidation: {e}")
        return False


async def register(consumer):
    """Регистрация consumers для событий profile-service"""
    await consumer.consume_user_events(
        event_type=EventType.USER_PROFILE_UPDATED,
        callback=handle_profile_updated
    )
    logger.info("Profile event consumer registered in matching-service")