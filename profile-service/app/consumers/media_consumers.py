# profile-service/app/consumers/media_consumers.py
from datetime import datetime
from typing import Dict, Any

from shared.events.schemas import EventType, BaseEvent
from app.services.rabbitmq import rabbitmq_consumer
from app.database.session import async_session_factory
from app.database.models import BasicProfile
from app.core.config import settings
from app.core.logger import logger
from sqlalchemy import select, update


async def handle_avatar_uploaded(event: Dict[str, Any]) -> bool:
    """Обработка события загрузки аватарки"""
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        avatar_url = user_data.get("url")
        thumbnail_url = user_data.get("thumbnail_url")
        is_current = user_data.get("is_current", True)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in AVATAR_UPLOADED event")
            return False
        
        if not is_current:
            logger.info(f"Skipping avatar update for {keycloak_id} - not current")
            return True
        
        logger.info(f"Processing AVATAR_UPLOADED for {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = (
                update(BasicProfile)
                .where(BasicProfile.keycloak_id == keycloak_id)
                .values(
                    avatar_url=avatar_url,
                    thumbnail_url=thumbnail_url,
                    updated_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount == 0:
                logger.warning(f"Profile not found for user {keycloak_id}")
                return True
        
        logger.info(f"Updated avatar URL for user {keycloak_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar uploaded event: {e}", exc_info=True)
        return False


async def handle_avatar_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления аватарки"""
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_current = user_data.get("is_current", False)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in AVATAR_DELETED event")
            return False
        
        # Обновляем профиль только если удаляется текущая аватарка
        if not is_current:
            logger.info(f"Skipping avatar deletion for {keycloak_id} - not current")
            return True
        
        logger.info(f"Processing AVATAR_DELETED for {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = (
                update(BasicProfile)
                .where(BasicProfile.keycloak_id == keycloak_id)
                .values(
                    avatar_url=None,
                    thumbnail_url=None,
                    updated_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount == 0:
                logger.warning(f"Profile not found for user {keycloak_id}")
                return True
        
        logger.info(f"Removed avatar URL for user {keycloak_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar deleted event: {e}", exc_info=True)
        return False


async def handle_avatar_updated(event: Dict[str, Any]) -> bool:
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        avatar_id = user_data.get("avatar_id")
        is_current = user_data.get("is_current", False)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in AVATAR_UPDATED event")
            return False
        
        # Нас интересует только установка аватарки как текущей
        if not is_current:
            logger.debug(f"Skipping avatar update for {keycloak_id} - not setting as current")
            return True
        
        logger.info(f"Processing AVATAR_UPDATED for {keycloak_id}, new current avatar: {avatar_id}")
        
        # Формируем URL для доступа к аватарке
        avatar_url = f"/media/avatar/{keycloak_id}?avatar_id={avatar_id}"
        thumbnail_url = f"/media/avatar/{keycloak_id}/thumbnail?avatar_id={avatar_id}"
        
        async with async_session_factory() as session:
            stmt = (
                update(BasicProfile)
                .where(BasicProfile.keycloak_id == keycloak_id)
                .values(
                    avatar_url=avatar_url,
                    thumbnail_url=thumbnail_url,
                    updated_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount == 0:
                logger.warning(f"Profile not found for user {keycloak_id}")
                return True
        
        logger.info(f"Updated avatar URLs for user {keycloak_id} to {avatar_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar updated event: {e}", exc_info=True)
        return False


async def register(consumer):
    """Регистрация consumers для событий от media-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_UPLOADED,
            callback=handle_avatar_uploaded
        )
        
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_DELETED,
            callback=handle_avatar_deleted
        )
        
        # НОВЫЙ consumer для события обновления аватарки
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_UPDATED,
            callback=handle_avatar_updated
        )
        
        logger.info("Media event consumers registered successfully in profile-service")
    except Exception as e:
        logger.error(f"Failed to register media consumers: {e}", exc_info=True)
        raise