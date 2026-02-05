from datetime import datetime
from typing import Dict, Any

from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.database.postgres.session import async_session_factory
from sqlalchemy import update, select
from app.database.postgres.models import ChatParticipant, Message
from app.core.config import settings
from app.core.logger import logger

async def handle_user_profile_updated(event: Dict[str, Any]) -> bool:
    """Обработка события обновления профиля пользователя"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        
        if not keycloak_id or "username" not in updated_fields:
            return True  # Нас интересуют только обновления username
        
        new_username = updated_fields["username"]
        
        logger.info(f"Updating username for {keycloak_id} to {new_username}")
        
        async with async_session_factory() as session:
            # Обновляем username в участниках чатов
            stmt_participants = (
                update(ChatParticipant)
                .where(ChatParticipant.keycloak_id == keycloak_id)
                .values(username=new_username)
            )
            await session.execute(stmt_participants)
            
            # Обновляем username в сообщениях
            stmt_messages = (
                update(Message)
                .where(Message.sender_keycloak_id == keycloak_id)
                .values(sender_username=new_username)
            )
            await session.execute(stmt_messages)
            
            await session.commit()
        
        logger.info(f"Username updated for {keycloak_id} in chat service")
        return True
        
    except Exception as e:
        logger.error(f"Error handling user profile update in chat service: {e}")
        return False

async def handle_user_deleted(event: Dict[str, Any]) -> bool:
    """Обработка события удаления пользователя"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        
        if not keycloak_id:
            return False
        
        logger.info(f"Handling user deletion for {keycloak_id} in chat service")
        
        async with async_session_factory() as session:
            # Помечаем, что пользователь вышел из всех чатов
            stmt = (
                update(ChatParticipant)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
                .values(left_at=datetime.utcnow())
            )
            await session.execute(stmt)
            
            await session.commit()
        
        logger.info(f"User {keycloak_id} marked as left from all chats")
        return True
        
    except Exception as e:
        logger.error(f"Error handling user deletion in chat service: {e}")
        return False

async def register(consumer):
    """Регистрация consumers для событий от user-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_UPDATED,
            callback=handle_user_profile_updated
        )
        
        await consumer.consume_user_events(
            event_type=EventType.USER_DELETED,
            callback=handle_user_deleted
        )
        
        logger.info("User event consumers registered successfully in chat service")
    except Exception as e:
        logger.error(f"Failed to register user consumers: {e}", exc_info=True)
        raise