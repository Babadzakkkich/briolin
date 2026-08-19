import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import (
    ChatNotFoundException,
    DatabaseException,
    MessageNotFoundException,
    PermissionDeniedException,
    RateLimitException,
    ValidationException,
)
from app.core.logger import logger
from app.database.mongo.session import get_mongo_db
from app.database.postgres.models import (
    Chat,
    ChatParticipant,
    ChatStatus,
    ChatType,
    Message,
    MessageReadStatus,
    MessageStatus,
)
from app.schemas.chat import (
    ChatCreate,
    ChatEvent,
    ChatResponse,
    ChatUpdate,
    MessageCreate,
    MessageReadStatusResponse,
    MessageResponse,
    MessageUpdate,
)
from app.services.matching_service_client import get_matching_client
from app.services.profile_service_client import get_profile_service_client
from app.services.user_service_client import get_user_service_client
from app.services.websocket_manager import websocket_manager
from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mongo_db = None
        self.user_client = get_user_service_client()
        self.profile_client = get_profile_service_client()

    async def _get_mongo_db(self):
        """Ленивая инициализация MongoDB"""
        if self.mongo_db is None:
            self.mongo_db = await get_mongo_db()
        return self.mongo_db

    async def _get_user_info(self, keycloak_id: str) -> Dict[str, str]:
        """Получение информации о пользователе из user-service (fallback)"""
        user_data = await self.user_client.get_user_by_keycloak_id(keycloak_id)
        if user_data:
            return {
                "username": user_data.get("username", keycloak_id),
                "keycloak_id": keycloak_id
            }
        logger.warning(f"Using fallback for user {keycloak_id}: user-service unavailable")
        return {
            "username": keycloak_id,
            "keycloak_id": keycloak_id
        }

    async def _get_profile_info(self, keycloak_id: str) -> Dict[str, Any]:
        """Получение полной информации о профиле из profile-service"""
        profile = await self.profile_client.get_profile_by_keycloak_id(keycloak_id)

        if profile and "basic" in profile:
            basic = profile["basic"]
            first_name = basic.get("first_name", "")
            last_name = basic.get("last_name", "")

            display_name = f"{first_name} {last_name}".strip()
            if not display_name:
                display_name = keycloak_id[:8]

            return {
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "avatar_url": basic.get("avatar_url"),
                "keycloak_id": keycloak_id,
                "username": basic.get("username")
            }

        logger.warning(f"Profile not found for {keycloak_id}, using fallback")
        user_info = await self._get_user_info(keycloak_id)
        return {
            "display_name": user_info.get("username", keycloak_id[:8]),
            "first_name": "",
            "last_name": "",
            "avatar_url": None,
            "keycloak_id": keycloak_id,
            "username": user_info.get("username", keycloak_id[:8])
        }

    async def _get_display_name(self, keycloak_id: str) -> str:
        """Быстрое получение только отображаемого имени"""
        return await self.profile_client.get_display_name(keycloak_id)

    async def _check_chat_permission(self, chat_id: uuid.UUID, keycloak_id: str) -> Chat:
        """Проверка доступа пользователя к чату"""
        stmt = (
            select(Chat)
            .options(
                selectinload(Chat.participants),
                selectinload(Chat.messages).selectinload(Message.read_statuses)
            )
            .where(Chat.id == chat_id)
        )
        result = await self.db.execute(stmt)
        chat = result.scalar_one_or_none()

        if not chat:
            raise ChatNotFoundException(f"Chat {chat_id} not found")

        if chat.status == ChatStatus.BLOCKED:
            raise PermissionDeniedException("Chat is blocked")

        is_participant = any(
            p.keycloak_id == keycloak_id and p.left_at is None
            for p in chat.participants
        )

        if not is_participant:
            raise PermissionDeniedException("You are not a participant of this chat")

        return chat

    async def _get_or_create_direct_chat(
        self,
        creator_keycloak_id: str,
        other_user_id: str
    ) -> Optional[Chat]:
        """Проверяет существование личного чата между двумя пользователями"""
        stmt = (
            select(Chat)
            .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
            .where(
                Chat.type == ChatType.DIRECT,
                ChatParticipant.keycloak_id.in_([creator_keycloak_id, other_user_id]),
                ChatParticipant.left_at.is_(None)
            )
            .group_by(Chat.id)
            .having(func.count(ChatParticipant.id) == 2)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _generate_direct_chat_name(
        self,
        for_user_keycloak_id: str,
        partner_keycloak_id: str
    ) -> Tuple[str, Optional[str]]:
        """Генерирует название чата и аватарку для личного чата"""
        partner_profile = await self._get_profile_info(partner_keycloak_id)
        name = partner_profile["display_name"]
        avatar_url = partner_profile["avatar_url"]
        return name, avatar_url

    async def create_chat(
        self,
        chat_data: ChatCreate,
        creator_keycloak_id: str,
        creator_username: str
    ) -> ChatResponse:
        """Создание нового чата"""
        try:
            if chat_data.type == ChatType.DIRECT and len(chat_data.participant_ids) != 1:
                raise ValidationException("Direct chat must have exactly one other participant")

            if chat_data.type == ChatType.GROUP and len(chat_data.participant_ids) < 1:
                raise ValidationException("Group chat must have at least one other participant")

            other_user_id = None
            if chat_data.type == ChatType.DIRECT:
                other_user_id = chat_data.participant_ids[0]

                existing_chat = await self._get_or_create_direct_chat(
                    creator_keycloak_id,
                    other_user_id
                )

                if existing_chat:
                    logger.info(f"Returning existing direct chat: {existing_chat.id}")
                    return await self._format_chat_response(existing_chat, creator_keycloak_id)

            all_participant_ids = [creator_keycloak_id] + chat_data.participant_ids
            unique_participant_ids = list(dict.fromkeys(all_participant_ids))

            participants_profiles = {}
            for pid in unique_participant_ids:
                profile = await self._get_profile_info(pid)
                participants_profiles[pid] = profile
                logger.debug(f"Profile for {pid}: display_name={profile.get('display_name')}")

            new_chat = Chat(
                id=uuid.uuid4(),
                type=chat_data.type,
                status=ChatStatus.ACTIVE
            )

            if chat_data.type == ChatType.DIRECT:
                other_profile = participants_profiles[other_user_id]
                new_chat.name = other_profile["display_name"]
                new_chat.avatar_url = other_profile["avatar_url"]

                new_chat.direct_chat_partner_mapping = json.dumps({
                    creator_keycloak_id: other_user_id,
                    other_user_id: creator_keycloak_id
                })
            else:
                new_chat.name = chat_data.name
                new_chat.description = chat_data.description
                new_chat.avatar_url = chat_data.avatar_url

            self.db.add(new_chat)

            for pid in unique_participant_ids:
                is_admin = (pid == creator_keycloak_id)
                profile = participants_profiles[pid]
                display_name = profile["display_name"]
                avatar_url = profile["avatar_url"]

                username = profile.get("username")
                if not username or username == pid:
                    user_info = await self._get_user_info(pid)
                    username = user_info.get("username", pid[:8])

                participant = ChatParticipant(
                    chat_id=new_chat.id,
                    keycloak_id=pid,
                    display_name=display_name,
                    username=username,
                    is_admin=is_admin,
                    avatar_url=avatar_url
                )
                self.db.add(participant)

            await self.db.commit()
            await self.db.refresh(new_chat)

            logger.info(f"Chat created: {new_chat.id} by {creator_keycloak_id}")

            await self._notify_chat_event(
                new_chat.id,
                "chat_created",
                {
                    "chat_id": str(new_chat.id),
                    "creator_id": creator_keycloak_id,
                    "type": chat_data.type.value,
                    "participants": list(unique_participant_ids)
                }
            )

            return await self._format_chat_response(new_chat, creator_keycloak_id)

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating chat: {e}")
            raise DatabaseException("Failed to create chat")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating chat: {e}")
            raise

    async def get_chat(self, chat_id: uuid.UUID, keycloak_id: str) -> ChatResponse:
        """Получение информации о чате"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)
        return await self._format_chat_response(chat, keycloak_id)

    async def get_chat_match_answers(
        self,
        chat_id: uuid.UUID,
        keycloak_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получение ответов на вопросы для чата.
        Если чат создан из мэтча — ходит в matching-service за ответами.
        """
        chat = await self._check_chat_permission(chat_id, keycloak_id)

        if not chat.match_id:
            return None

        matching_client = get_matching_client()
        return await matching_client.get_match_answers(
            match_id=chat.match_id,
            keycloak_id=keycloak_id
        )

    async def list_chats(
        self,
        keycloak_id: str,
        skip: int = 0,
        limit: int = 50,
        chat_type: Optional[ChatType] = None,
        status: Optional[ChatStatus] = None
    ) -> Tuple[List[ChatResponse], int]:
        """Получение списка чатов пользователя"""
        try:
            subquery = (
                select(ChatParticipant.chat_id)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
                .subquery()
            )

            query = (
                select(Chat)
                .options(selectinload(Chat.participants))
                .join(subquery, Chat.id == subquery.c.chat_id)
            )

            if chat_type:
                query = query.where(Chat.type == chat_type)

            if status:
                query = query.where(Chat.status == status)
            else:
                query = query.where(Chat.status != ChatStatus.BLOCKED)

            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()

            query = (
                query
                .outerjoin(Message, Chat.id == Message.chat_id)
                .group_by(Chat.id)
                .order_by(func.coalesce(func.max(Message.created_at), Chat.created_at).desc())
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            chats = result.scalars().all()

            chat_responses = []
            for chat in chats:
                chat_response = await self._format_chat_response(chat, keycloak_id)
                chat_responses.append(chat_response)

            return chat_responses, total

        except Exception as e:
            logger.error(f"Error listing chats: {e}")
            raise DatabaseException("Failed to list chats")

    async def update_chat(
        self,
        chat_id: uuid.UUID,
        chat_data: ChatUpdate,
        keycloak_id: str
    ) -> ChatResponse:
        """Обновление информации о чате"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)

        if chat.type == ChatType.DIRECT:
            raise PermissionDeniedException("Cannot update direct chat")

        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )

        if not is_admin:
            raise PermissionDeniedException("Only chat admins can update chat")

        try:
            update_data = chat_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(chat, field) and value is not None:
                    setattr(chat, field, value)

            await self.db.commit()
            await self.db.refresh(chat)

            logger.info(f"Chat updated: {chat_id} by {keycloak_id}")

            await self._notify_chat_event(
                chat_id,
                "chat_updated",
                {"chat_id": str(chat_id), "updated_fields": list(update_data.keys())}
            )

            return await self._format_chat_response(chat, keycloak_id)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating chat: {e}")
            raise DatabaseException("Failed to update chat")

    async def delete_chat(self, chat_id: uuid.UUID, keycloak_id: str) -> bool:
        """Полное удаление чата"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)

        if chat.type == ChatType.GROUP:
            is_admin = any(
                p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
                for p in chat.participants
            )
            if not is_admin:
                raise PermissionDeniedException("Only chat admins can delete group chat")

        try:
            chat_id_str = str(chat_id)

            try:
                mongo_db = await self._get_mongo_db()
                await mongo_db.messages.delete_many({"chat_id": chat_id_str})
                logger.debug(f"Deleted messages from MongoDB for chat {chat_id_str}")
            except Exception as e:
                logger.warning(f"Failed to delete messages from MongoDB: {e}")

            await self.db.delete(chat)
            await self.db.commit()

            logger.info(f"Chat deleted permanently: {chat_id_str} by {keycloak_id}")

            await self._notify_chat_event(
                chat_id,
                "chat_deleted",
                {"chat_id": chat_id_str, "deleted_by": keycloak_id, "permanent": True}
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting chat: {e}")
            raise DatabaseException("Failed to delete chat")

    async def send_message(
        self,
        chat_id: uuid.UUID,
        message_data: MessageCreate,
        sender_keycloak_id: str,
        sender_username: str
    ) -> MessageResponse:
        """Отправка сообщения в чат"""
        if not await websocket_manager.check_rate_limit(sender_keycloak_id):
            raise RateLimitException("Message rate limit exceeded")

        chat = await self._check_chat_permission(chat_id, sender_keycloak_id)

        try:
            sender_display_name = await self._get_display_name(sender_keycloak_id)

            new_message = Message(
                id=uuid.uuid4(),
                chat_id=chat_id,
                sender_keycloak_id=sender_keycloak_id,
                sender_display_name=sender_display_name,
                sender_username=sender_username,
                content=message_data.content,
                message_type=message_data.message_type,
                reply_to_id=message_data.reply_to_id,
                media_url=message_data.media_url,
                media_type=message_data.media_type,
                file_size=message_data.file_size,
                status=MessageStatus.SENT
            )

            self.db.add(new_message)
            chat.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(new_message)

            logger.info(f"Message sent: {new_message.id} in chat {chat_id}")

            message_response = await self._format_message_response(new_message, sender_keycloak_id)

            ws_message = {
                "type": "message",
                "chat_id": str(chat_id),
                "message": message_response.model_dump(mode='json'),
                "sender_id": sender_keycloak_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            await websocket_manager.broadcast_to_chat(
                ws_message,
                str(chat_id),
                exclude_user=sender_keycloak_id
            )

            await self._save_message_to_mongo(message_response)

            return message_response

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error sending message: {e}")
            raise DatabaseException("Failed to send message")

    async def get_messages(
        self,
        chat_id: uuid.UUID,
        keycloak_id: str,
        skip: int = 0,
        limit: int = 50,
        before: Optional[datetime] = None
    ) -> Tuple[List[MessageResponse], int]:
        """Получение сообщений из чата с правильным статусом прочтения"""
        await self._check_chat_permission(chat_id, keycloak_id)

        try:
            query = (
                select(Message)
                .options(selectinload(Message.read_statuses))
                .where(Message.chat_id == chat_id)
            )

            if before:
                query = query.where(Message.created_at < before)

            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()

            query = (
                query
                .order_by(desc(Message.created_at))
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            messages = result.scalars().all()

            # Автоматически отмечаем как прочитанные сообщения, полученные от других
            unread_messages = [
                msg for msg in messages
                if msg.sender_keycloak_id != keycloak_id
                and not msg.is_read_by(keycloak_id)
            ]

            if unread_messages:
                await self.mark_messages_as_read(
                    chat_id,
                    keycloak_id,
                    [msg.id for msg in unread_messages],
                    notify=False  # Не отправляем уведомления при пагинации
                )

            message_responses = []
            for message in reversed(messages):
                message_response = await self._format_message_response(message, keycloak_id)
                message_responses.append(message_response)

            return message_responses, total

        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise DatabaseException("Failed to get messages")

    async def delete_message(self, message_id: uuid.UUID, keycloak_id: str) -> bool:
        """Удаление сообщения"""
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await self.db.execute(stmt)
            message = result.scalar_one_or_none()

            if not message:
                raise MessageNotFoundException()

            chat = await self._check_chat_permission(message.chat_id, keycloak_id)

            is_sender = message.sender_keycloak_id == keycloak_id
            is_admin = any(
                p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
                for p in chat.participants
            )

            if not (is_sender or is_admin):
                raise PermissionDeniedException("Cannot delete this message")

            # Удаляем из MongoDB
            try:
                mongo_db = await self._get_mongo_db()
                await mongo_db.messages.delete_one({"message_id": str(message_id)})
            except Exception as e:
                logger.warning(f"Failed to delete message from MongoDB: {e}")

            await self.db.delete(message)
            await self.db.commit()

            logger.info(f"Message deleted: {message_id} by {keycloak_id}")

            ws_message = {
                "type": "message_deleted",
                "chat_id": str(message.chat_id),
                "message_id": str(message_id),
                "deleted_by": keycloak_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            await websocket_manager.broadcast_to_chat(
                ws_message,
                str(message.chat_id)
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting message: {e}")
            raise DatabaseException("Failed to delete message")

    async def update_message(
        self,
        message_id: uuid.UUID,
        message_data: MessageUpdate,
        sender_keycloak_id: str
    ) -> MessageResponse:
        """Редактирование существующего сообщения"""
        try:
            stmt = (
                select(Message)
                .options(selectinload(Message.read_statuses))
                .where(Message.id == message_id)
            )
            result = await self.db.execute(stmt)
            message = result.scalar_one_or_none()

            if not message:
                raise MessageNotFoundException()

            if message.sender_keycloak_id != sender_keycloak_id:
                raise PermissionDeniedException("Only message sender can edit the message")

            message_age = datetime.utcnow() - message.created_at
            if message_age > timedelta(hours=24):
                raise PermissionDeniedException("Message can only be edited within 24 hours")

            if message.status == MessageStatus.FAILED:
                raise PermissionDeniedException("Cannot edit deleted message")

            message.content = message_data.content
            message.is_edited = True

            await self.db.commit()
            await self.db.refresh(message)

            logger.info(f"Message updated: {message_id} by {sender_keycloak_id}")

            message_response = await self._format_message_response(message, sender_keycloak_id)

            ws_message = {
                "type": "message_updated",
                "chat_id": str(message.chat_id),
                "message": message_response.model_dump(mode='json'),
                "sender_id": sender_keycloak_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            await websocket_manager.broadcast_to_chat(
                ws_message,
                str(message.chat_id),
                exclude_user=sender_keycloak_id
            )

            await self._update_message_in_mongo(message_response)

            return message_response

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating message: {e}")
            raise DatabaseException("Failed to update message")

    async def mark_messages_as_read(
        self,
        chat_id: uuid.UUID,
        keycloak_id: str,
        message_ids: List[uuid.UUID],
        notify: bool = True
    ) -> bool:
        """
        Отметка сообщений как прочитанных с правильным many-to-many подходом.

        Args:
            chat_id: ID чата
            keycloak_id: ID пользователя
            message_ids: Список ID сообщений для отметки
            notify: Отправлять ли WebSocket уведомления
        """
        await self._check_chat_permission(chat_id, keycloak_id)

        if not message_ids:
            return True

        try:
            # Получаем сообщения, которые нужно отметить
            stmt = (
                select(Message)
                .where(
                    Message.id.in_(message_ids),
                    Message.chat_id == chat_id,
                    Message.sender_keycloak_id != keycloak_id  # Не отмечаем свои
                )
            )
            result = await self.db.execute(stmt)
            messages = result.scalars().all()

            if not messages:
                logger.debug(f"No messages to mark as read for {keycloak_id} in chat {chat_id}")
                return True

            # Получаем существующие статусы прочтения
            existing_stmt = select(MessageReadStatus).where(
                MessageReadStatus.message_id.in_([msg.id for msg in messages]),
                MessageReadStatus.keycloak_id == keycloak_id
            )
            existing_result = await self.db.execute(existing_stmt)
            existing_statuses = existing_result.scalars().all()
            existing_message_ids = {str(rs.message_id) for rs in existing_statuses}

            # Создаем новые статусы для сообщений, которых еще нет
            new_statuses = []
            marked_message_ids = []

            for message in messages:
                if str(message.id) not in existing_message_ids:
                    read_status = MessageReadStatus(
                        message_id=message.id,
                        keycloak_id=keycloak_id,
                        read_at=datetime.utcnow()
                    )
                    self.db.add(read_status)
                    new_statuses.append(read_status)
                    marked_message_ids.append(message.id)

            if new_statuses:
                await self.db.commit()
                logger.info(
                    f"Marked {len(new_statuses)} messages as read for {keycloak_id} "
                    f"in chat {chat_id}"
                )

                # Отправляем WebSocket уведомления
                if notify and marked_message_ids:
                    for message_id in marked_message_ids[:10]:  # Ограничиваем количество уведомлений
                        await websocket_manager.send_read_receipt(
                            chat_id,
                            keycloak_id,
                            message_id
                        )

                    # Если много сообщений, отправляем одно массовое уведомление
                    if len(marked_message_ids) > 10:
                        bulk_receipt = {
                            "type": "bulk_read_receipt",
                            "chat_id": str(chat_id),
                            "user_id": keycloak_id,
                            "message_ids": [str(mid) for mid in marked_message_ids],
                            "read_at": datetime.utcnow().isoformat()
                        }
                        await websocket_manager.broadcast_to_chat(
                            bulk_receipt,
                            str(chat_id),
                            exclude_user=keycloak_id
                        )
            else:
                logger.debug(f"No new messages to mark as read for {keycloak_id}")

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking messages as read: {e}")
            raise DatabaseException("Failed to mark messages as read")

    async def get_message_read_status(
        self,
        chat_id: uuid.UUID,
        message_id: uuid.UUID,
        keycloak_id: str
    ) -> MessageReadStatusResponse:
        """Получение информации о том, кто прочитал сообщение"""
        await self._check_chat_permission(chat_id, keycloak_id)

        try:
            stmt = (
                select(Message)
                .options(selectinload(Message.read_statuses))
                .where(
                    Message.id == message_id,
                    Message.chat_id == chat_id
                )
            )
            result = await self.db.execute(stmt)
            message = result.scalar_one_or_none()

            if not message:
                raise MessageNotFoundException(f"Message {message_id} not found")

            # Получаем информацию о пользователях, прочитавших сообщение
            read_by_users = []
            for read_status in message.read_statuses:
                # Получаем профиль пользователя
                profile = await self._get_profile_info(read_status.keycloak_id)
                read_by_users.append({
                    "keycloak_id": read_status.keycloak_id,
                    "display_name": profile.get("display_name", read_status.keycloak_id[:8]),
                    "avatar_url": profile.get("avatar_url"),
                    "read_at": read_status.read_at.isoformat()
                })

            return MessageReadStatusResponse(
                message_id=message_id,
                read_by_users=read_by_users,
                total_read_count=len(read_by_users)
            )

        except Exception as e:
            logger.error(f"Error getting message read status: {e}")
            raise DatabaseException("Failed to get message read status")

    async def add_participant(self, chat_id: uuid.UUID, keycloak_id: str, new_user_id: str) -> bool:
        """Добавление участника в чат"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)

        if chat.type != ChatType.GROUP:
            raise ValidationException("Cannot add participants to non-group chat")

        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )

        if not is_admin:
            raise PermissionDeniedException("Only chat admins can add participants")

        try:
            existing_participant = any(
                p.keycloak_id == new_user_id and p.left_at is None
                for p in chat.participants
            )

            if existing_participant:
                raise ValidationException("User is already a participant")

            new_user_profile = await self._get_profile_info(new_user_id)

            new_participant = ChatParticipant(
                chat_id=chat_id,
                keycloak_id=new_user_id,
                display_name=new_user_profile["display_name"],
                username=new_user_profile.get("username", new_user_id),
                is_admin=False,
                avatar_url=new_user_profile.get("avatar_url")
            )

            self.db.add(new_participant)
            await self.db.commit()

            logger.info(f"User {new_user_id} added to chat {chat_id}")

            await self._notify_chat_event(
                chat_id,
                "user_joined",
                {
                    "chat_id": str(chat_id),
                    "user_id": new_user_id,
                    "added_by": keycloak_id,
                    "display_name": new_user_profile["display_name"]
                }
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding participant: {e}")
            raise DatabaseException("Failed to add participant")

    async def remove_participant(self, chat_id: uuid.UUID, keycloak_id: str, user_to_remove_id: str) -> bool:
        """Удаление участника из чата"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)

        if chat.type != ChatType.GROUP:
            raise ValidationException("Cannot remove participants from non-group chat")

        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )

        is_self = user_to_remove_id == keycloak_id

        if not (is_admin or is_self):
            raise PermissionDeniedException("Cannot remove this participant")

        try:
            stmt = select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.keycloak_id == user_to_remove_id,
                ChatParticipant.left_at.is_(None)
            )
            result = await self.db.execute(stmt)
            participant = result.scalar_one_or_none()

            if not participant:
                raise ValidationException("Participant not found")

            participant.left_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"User {user_to_remove_id} removed from chat {chat_id}")

            await self._notify_chat_event(
                chat_id,
                "user_left",
                {
                    "chat_id": str(chat_id),
                    "user_id": user_to_remove_id,
                    "removed_by": keycloak_id
                }
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing participant: {e}")
            raise DatabaseException("Failed to remove participant")

    async def search_messages(
        self,
        keycloak_id: str,
        query: str,
        chat_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[MessageResponse]:
        """Поиск сообщений по тексту"""
        try:
            mongo_db = await self._get_mongo_db()
            collection = mongo_db.messages

            search_filter = {"content": {"$regex": query, "$options": "i"}}

            # Получаем ID чатов, к которым имеет доступ пользователь
            user_chat_ids = await self._get_user_chat_ids(keycloak_id)

            if chat_id:
                # Проверяем доступ к конкретному чату
                if str(chat_id) not in user_chat_ids:
                    raise PermissionDeniedException("You don't have access to this chat")
                search_filter["chat_id"] = str(chat_id)
            else:
                # Ищем только в чатах пользователя
                if not user_chat_ids:
                    return []
                search_filter["chat_id"] = {"$in": user_chat_ids}

            cursor = collection.find(search_filter)
            cursor.sort("created_at", -1)
            cursor.skip(skip).limit(limit)

            mongo_messages = await cursor.to_list(length=limit)

            message_responses = []
            for msg in mongo_messages:
                stmt = (
                    select(Message)
                    .options(selectinload(Message.read_statuses))
                    .where(Message.id == uuid.UUID(msg["message_id"]))
                )
                result = await self.db.execute(stmt)
                message = result.scalar_one_or_none()

                if message:
                    message_response = await self._format_message_response(message, keycloak_id)
                    message_responses.append(message_response)

            return message_responses

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise DatabaseException("Failed to search messages")

    async def _format_chat_response(self, chat: Chat, keycloak_id: str) -> ChatResponse:
        """Форматирование ответа чата с информацией о мэтче и вопросах"""
        stmt = (
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_message = result.scalar_one_or_none()

        # Подсчет непрочитанных
        unread_stmt = (
            select(func.count())
            .select_from(Message)
            .outerjoin(
                MessageReadStatus,
                and_(
                    MessageReadStatus.message_id == Message.id,
                    MessageReadStatus.keycloak_id == keycloak_id
                )
            )
            .where(
                Message.chat_id == chat.id,
                Message.sender_keycloak_id != keycloak_id,
                MessageReadStatus.id.is_(None)
            )
        )
        unread_result = await self.db.execute(unread_stmt)
        unread_count = unread_result.scalar_one()

        last_message_data = None
        if last_message:
            last_message_data = {
                "id": str(last_message.id),
                "content": last_message.content,
                "sender_id": last_message.sender_keycloak_id,
                "sender_display_name": last_message.sender_display_name,
                "created_at": last_message.created_at.isoformat(),
                "type": last_message.message_type
            }

        participants = []
        chat_name = chat.name
        chat_avatar = chat.avatar_url

        if chat.type == ChatType.DIRECT:
            partner_id = None

            if chat.direct_chat_partner_mapping:
                try:
                    mapping = json.loads(chat.direct_chat_partner_mapping)
                    partner_id = mapping.get(keycloak_id)
                except json.JSONDecodeError:
                    pass

            if not partner_id:
                for p in chat.participants:
                    if p.keycloak_id != keycloak_id and p.left_at is None:
                        partner_id = p.keycloak_id
                        break

            if partner_id:
                partner_profile = await self._get_profile_info(partner_id)
                chat_name = partner_profile["display_name"]
                # Используем thumbnail аватарку партнёра для чата
                chat_avatar = partner_profile.get("thumbnail_url") or partner_profile.get("avatar_url")

            for p in chat.participants:
                if p.left_at is None:
                    participants.append({
                        "keycloak_id": p.keycloak_id,
                        "display_name": p.display_name,
                        "username": p.username,
                        "is_admin": p.is_admin,
                        "notifications_enabled": p.notifications_enabled,
                        "avatar_url": p.avatar_url
                    })
        else:
            for p in chat.participants:
                if p.left_at is None:
                    participants.append({
                        "keycloak_id": p.keycloak_id,
                        "display_name": p.display_name,
                        "username": p.username,
                        "is_admin": p.is_admin,
                        "notifications_enabled": p.notifications_enabled,
                        "avatar_url": p.avatar_url
                    })

        return ChatResponse(
            id=chat.id,
            type=chat.type,
            status=chat.status,
            name=chat_name,
            description=chat.description,
            avatar_url=chat_avatar,
            participants=participants,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            last_message=last_message_data,
            unread_count=unread_count,
            match_id=chat.match_id
        )

    async def _format_message_response(
        self,
        message: Message,
        current_user_id: str
    ) -> MessageResponse:
        """Форматирование ответа сообщения с информацией о прочтении"""
        is_read_by_me = message.is_read_by(current_user_id)

        # Определяем статус для ответа
        if message.sender_keycloak_id == current_user_id:
            # Для отправителя: показываем реальный статус доставки
            status = message.status
        else:
            # Для получателя: DELIVERED по умолчанию (статус READ не используется)
            # В будущем можно добавить READ, если будет нужно
            status = MessageStatus.DELIVERED

        return MessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            sender_keycloak_id=message.sender_keycloak_id,
            sender_display_name=message.sender_display_name,
            sender_username=message.sender_username,
            content=message.content,
            message_type=message.message_type,
            status=status,
            is_edited=message.is_edited,
            reply_to_id=message.reply_to_id,
            media_url=message.media_url,
            media_type=message.media_type,
            file_size=message.file_size,
            created_at=message.created_at,
            updated_at=message.updated_at,
            read_by=message.read_by_users,
            read_count=message.read_by_count,
            is_read_by_me=is_read_by_me
        )

    async def _notify_chat_event(self, chat_id: uuid.UUID, event_type: str, data: Dict[str, Any]):
        """Отправка события о чате через WebSocket"""
        event = ChatEvent(
            event_type=event_type,
            chat_id=chat_id,
            data=data,
            timestamp=datetime.utcnow()
        )

        ws_message = {
            "type": "chat_update",
            "chat_id": str(chat_id),
            "event": event.model_dump(mode='json'),
            "timestamp": datetime.utcnow().isoformat()
        }

        await websocket_manager.broadcast_to_chat(ws_message, str(chat_id))

    async def _save_message_to_mongo(self, message: MessageResponse):
        """Сохранение сообщения в MongoDB для поиска"""
        try:
            mongo_db = await self._get_mongo_db()
            collection = mongo_db.messages

            mongo_doc = {
                "message_id": str(message.id),
                "chat_id": str(message.chat_id),
                "sender_id": message.sender_keycloak_id,
                "sender_display_name": message.sender_display_name,
                "sender_username": message.sender_username,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat(),
                "updated_at": message.updated_at.isoformat(),
                "is_edited": message.is_edited
            }

            await collection.insert_one(mongo_doc)

        except Exception as e:
            logger.error(f"Error saving message to MongoDB: {e}")

    async def _update_message_in_mongo(self, message: MessageResponse):
        """Обновление сообщения в MongoDB для поиска"""
        try:
            mongo_db = await self._get_mongo_db()
            collection = mongo_db.messages

            await collection.update_one(
                {"message_id": str(message.id)},
                {
                    "$set": {
                        "content": message.content,
                        "is_edited": message.is_edited,
                        "updated_at": message.updated_at.isoformat()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error updating message in MongoDB: {e}")

    async def _get_user_chat_ids(self, keycloak_id: str) -> List[str]:
        """Получение списка ID чатов пользователя"""
        try:
            stmt = (
                select(ChatParticipant.chat_id)
                .where(
                    ChatParticipant.keycloak_id == keycloak_id,
                    ChatParticipant.left_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            chat_ids = result.scalars().all()

            return [str(chat_id) for chat_id in chat_ids]

        except Exception as e:
            logger.error(f"Error getting user chat ids: {e}")
            return []
