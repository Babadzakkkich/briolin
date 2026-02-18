from datetime import datetime
from typing import Dict, Any

from shared.events.schemas import EventType, BaseEvent
from app.services.rabbitmq import rabbitmq_consumer
from app.database.postgres.session import async_session_factory
from sqlalchemy import update, select
from app.database.postgres.models import ChatParticipant, Message
from app.core.config import settings
from app.core.logger import logger
from app.services.profile_service_client import get_profile_service_client


async def handle_user_profile_updated(event: Dict[str, Any]) -> bool:
    """Обработка события обновления профиля пользователя - обновляем display_name в чатах"""
    try:
        base_event = BaseEvent(**event)

        # Проверяем, не обрабатывали ли мы уже это событие
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True

        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        updated_fields = user_data.get("updated_fields", {})
        source_service = user_data.get("source_service", "unknown")

        if not keycloak_id:
            logger.error("Missing keycloak_id in user profile updated event")
            return False

        logger.info(f"Received profile update event from {source_service} for {keycloak_id}")
        logger.debug(f"Updated fields: {list(updated_fields.keys())}")

        # Проверяем, обновлялось ли имя или фамилия
        name_fields_updated = any(field in updated_fields for field in ["first_name", "last_name"])
        
        if not name_fields_updated:
            logger.debug(f"No name-related fields updated for {keycloak_id}, skipping")
            return True

        # Получаем новое отображаемое имя из profile-service
        profile_client = get_profile_service_client()
        new_display_name = await profile_client.get_display_name(keycloak_id)

        if not new_display_name or new_display_name == keycloak_id[:8]:
            # Пробуем получить из updated_fields напрямую
            if "first_name" in updated_fields or "last_name" in updated_fields:
                first = updated_fields.get("first_name", "")
                last = updated_fields.get("last_name", "")
                new_display_name = f"{first} {last}".strip()
                
                if not new_display_name:
                    logger.warning(f"Could not construct display name for {keycloak_id}, skipping update")
                    return True
            else:
                logger.warning(f"Could not get valid display name for {keycloak_id}, skipping update")
                return True

        logger.info(f"Updating display_name for {keycloak_id} to '{new_display_name}'")

        async with async_session_factory() as session:
            # Обновляем display_name в участниках чатов
            stmt_participants = (
                update(ChatParticipant)
                .where(ChatParticipant.keycloak_id == keycloak_id)
                .values(display_name=new_display_name)
            )
            result = await session.execute(stmt_participants)
            participants_updated = result.rowcount

            # Обновляем display_name в сообщениях
            stmt_messages = (
                update(Message)
                .where(Message.sender_keycloak_id == keycloak_id)
                .values(sender_display_name=new_display_name)
            )
            result = await session.execute(stmt_messages)
            messages_updated = result.rowcount

            await session.commit()

        logger.info(
            f"Profile updated for {keycloak_id} in chat service: "
            f"participants={participants_updated}, messages={messages_updated}"
        )
        return True

    except Exception as e:
        logger.error(f"Error handling user profile update in chat service: {e}", exc_info=True)
        return False


async def register(consumer):
    """Регистрация consumers для событий от profile-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.USER_PROFILE_UPDATED,
            callback=handle_user_profile_updated
        )

        logger.info("Profile event consumers registered successfully in chat service")
    except Exception as e:
        logger.error(f"Failed to register profile consumers: {e}", exc_info=True)
        raise