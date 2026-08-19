import json
import uuid
from typing import Dict, Any
from datetime import datetime

from shared.events.schemas import EventType, BaseEvent
from app.services.rabbitmq import rabbitmq_consumer
from app.database.postgres.session import async_session_factory
from app.database.postgres.models import Chat, ChatParticipant, ChatType, ChatStatus
from app.services.profile_service_client import get_profile_service_client
from app.services.websocket_manager import websocket_manager
from app.core.config import settings
from app.core.logger import logger
from sqlalchemy import func, select, and_


async def handle_match_created(event: Dict[str, Any]) -> bool:
    """
    Обработка события создания матча от matching-service.
    Создаёт личный чат между двумя пользователями и сохраняет ID матча.
    """
    try:
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by chat-service")
            return True
        
        user_data = event.get("user_data", {})
        user1_id = user_data.get("user1_id")
        user2_id = user_data.get("user2_id")
        
        if not user1_id or not user2_id:
            logger.error(f"Missing user IDs in match.created event: {user_data}")
            return False
        
        logger.info(f"Processing match.created event: creating chat between {user1_id} and {user2_id}")
        
        profile_client = get_profile_service_client()
        
        display_name1 = await profile_client.get_display_name(user1_id)
        display_name2 = await profile_client.get_display_name(user2_id)
        
        profile1 = await profile_client.get_profile_by_keycloak_id(user1_id)
        profile2 = await profile_client.get_profile_by_keycloak_id(user2_id)
        
        avatar1 = None
        avatar2 = None
        username1 = None
        username2 = None
        
        if profile1 and "basic" in profile1:
            # Для чатов используем thumbnail
            avatar1 = profile1["basic"].get("thumbnail_url") or profile1["basic"].get("avatar_url")
            username1 = profile1["basic"].get("username")
        if profile2 and "basic" in profile2:
            # Для чатов используем thumbnail
            avatar2 = profile2["basic"].get("thumbnail_url") or profile2["basic"].get("avatar_url")
            username2 = profile2["basic"].get("username")
        
        async with async_session_factory() as session:
            # Проверяем существующий чат
            stmt = (
                select(Chat)
                .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
                .where(
                    Chat.type == ChatType.DIRECT,
                    ChatParticipant.keycloak_id.in_([user1_id, user2_id]),
                    ChatParticipant.left_at.is_(None)
                )
                .group_by(Chat.id)
                .having(func.count(ChatParticipant.id) == 2)
            )
            result = await session.execute(stmt)
            existing_chat = result.scalar_one_or_none()
            
            if existing_chat:
                # Обновляем match_id у существующего чата
                if not existing_chat.match_id:
                    existing_chat.match_id = user_data.get("match_id")
                    await session.commit()
                    logger.info(f"Updated match_id for existing chat {existing_chat.id}: {existing_chat.match_id}")
                return True
            
            # Создаём новый чат
            new_chat = Chat(
                id=uuid.uuid4(),
                type=ChatType.DIRECT,
                status=ChatStatus.ACTIVE,
                match_id=user_data.get("match_id")
            )
            session.add(new_chat)
            await session.flush()
            
            participant1 = ChatParticipant(
                chat_id=new_chat.id,
                keycloak_id=user1_id,
                display_name=display_name1,
                username=username1,
                is_admin=False,
                avatar_url=avatar1
            )
            participant2 = ChatParticipant(
                chat_id=new_chat.id,
                keycloak_id=user2_id,
                display_name=display_name2,
                username=username2,
                is_admin=False,
                avatar_url=avatar2
            )
            session.add_all([participant1, participant2])
            
            direct_chat_mapping = {
                user1_id: user2_id,
                user2_id: user1_id
            }
            new_chat.direct_chat_partner_mapping = json.dumps(direct_chat_mapping)
            
            # Устанавливаем аватарку чата (thumbnail второго участника)
            # _format_chat_response переопределит для каждого пользователя
            new_chat.avatar_url = avatar2 or avatar1
            
            await session.commit()
            
            logger.info(f"Direct chat created for match: {new_chat.id} (match_id={new_chat.match_id})")
            
            # WebSocket уведомления
            chat_info = {
                "type": "chat_created",
                "chat_id": str(new_chat.id),
                "participants": [user1_id, user2_id],
                "created_by": "system",
                "has_match_answers": new_chat.match_id is not None,
                "match_id": new_chat.match_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket_manager.send_personal_message(chat_info, user1_id)
            await websocket_manager.send_personal_message(chat_info, user2_id)
            
            return True
            
    except Exception as e:
        logger.error(f"Error handling match.created event: {e}", exc_info=True)
        return False


async def register(consumer):
    """Регистрация consumer для событий матчей"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.MATCH_CREATED,
            callback=handle_match_created
        )
        
        logger.info("Match event consumer registered successfully in chat-service")
    except Exception as e:
        logger.error(f"Failed to register match consumer: {e}", exc_info=True)
        raise