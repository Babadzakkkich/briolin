from typing import Dict, Any

from shared.events.schemas import EventType, BaseEvent
from app.services.rabbitmq import rabbitmq_consumer
from app.database.postgres.session import async_session_factory
from app.database.postgres.models import Chat, ChatParticipant, ChatType
from app.core.config import settings
from app.core.logger import logger
from sqlalchemy import update, select
import json


async def handle_avatar_uploaded(event: Dict[str, Any]) -> bool:
    """
    Обработка события загрузки/обновления аватарки.
    Обновляет avatar_url в участниках чатов.
    """
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        avatar_url = user_data.get("url")
        thumbnail_url = user_data.get("thumbnail_url")
        is_current = user_data.get("is_current", False)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in avatar event")
            return False
        
        if not is_current:
            logger.info(f"Skipping avatar update for {keycloak_id[:8]}... - not current")
            return True
        
        # Используем thumbnail_url для аватарок в чатах
        new_avatar_url = thumbnail_url or avatar_url
        
        logger.info(f"Processing avatar update for {keycloak_id[:8]}... in chat-service")
        
        async with async_session_factory() as session:
            # Обновляем avatar_url участника во всех чатах
            stmt = (
                update(ChatParticipant)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
                .values(avatar_url=new_avatar_url)
            )
            result = await session.execute(stmt)
            updated_count = result.rowcount
            
            await session.commit()
            
        logger.info(f"Updated avatar for {keycloak_id[:8]}... in {updated_count} chat participants")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar uploaded event in chat service: {e}", exc_info=True)
        return False


async def handle_avatar_updated(event: Dict[str, Any]) -> bool:
    """
    Обработка события смены текущей аватарки.
    Обновляет avatar_url в участниках чатов.
    """
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        avatar_id = user_data.get("avatar_id")
        is_current = user_data.get("is_current", False)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in avatar updated event")
            return False
        
        if not is_current:
            logger.debug(f"Skipping avatar update for {keycloak_id[:8]}... - not setting as current")
            return True
        
        logger.info(f"Processing avatar change for {keycloak_id[:8]}..., new avatar: {avatar_id}")
        
        # Формируем URL для доступа к аватарке
        thumbnail_url = f"/media/avatar/{keycloak_id}/thumbnail?avatar_id={avatar_id}"
        
        async with async_session_factory() as session:
            # Обновляем avatar_url участника во всех чатах
            stmt = (
                update(ChatParticipant)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
                .values(avatar_url=thumbnail_url)
            )
            result = await session.execute(stmt)
            updated_count = result.rowcount
            
            await session.commit()
            
        logger.info(f"Updated avatar for {keycloak_id[:8]}... in {updated_count} chat participants")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar updated event in chat service: {e}", exc_info=True)
        return False


async def handle_avatar_deleted(event: Dict[str, Any]) -> bool:
    """
    Обработка события удаления аватарки.
    Устанавливает avatar_url в None для участника во всех чатах.
    """
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        is_current = user_data.get("is_current", False)
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in avatar deleted event")
            return False
        
        # Обновляем даже если не current, так как это может быть удаление current аватарки
        logger.info(f"Processing avatar deletion for {keycloak_id[:8]}... in chat-service")
        
        async with async_session_factory() as session:
            stmt = (
                update(ChatParticipant)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
                .values(avatar_url=None)
            )
            result = await session.execute(stmt)
            updated_count = result.rowcount
            
            await session.commit()
            
        logger.info(f"Removed avatar for {keycloak_id[:8]}... from {updated_count} chat participants")
        return True
        
    except Exception as e:
        logger.error(f"Error handling avatar deleted event in chat service: {e}", exc_info=True)
        return False


async def register(consumer):
    """Регистрация consumers для событий от media-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_UPLOADED,
            callback=handle_avatar_uploaded
        )
        
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_UPDATED,
            callback=handle_avatar_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.AVATAR_DELETED,
            callback=handle_avatar_deleted
        )
        
        logger.info("Media event consumers registered successfully in chat-service")
    except Exception as e:
        logger.error(f"Failed to register media consumers: {e}", exc_info=True)
        raise