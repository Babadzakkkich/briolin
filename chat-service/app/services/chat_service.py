import uuid
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.database.postgres.models import Chat, ChatParticipant, Message, ChatType, ChatStatus, MessageStatus
from app.database.mongo.session import get_mongo_db
from app.services.websocket_manager import websocket_manager
from app.services.user_service_client import get_user_service_client
from app.core.exceptions import (
    ChatNotFoundException,
    MessageNotFoundException,
    PermissionDeniedException,
    DatabaseException,
    RateLimitException,
    ValidationException
)
from app.core.logger import logger
from app.schemas.chat import (
    ChatCreate, ChatUpdate, MessageCreate,
    ChatResponse, MessageResponse, ChatEvent
)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mongo_db = None
        self.user_client = get_user_service_client()
    
    async def _get_mongo_db(self):
        """Ленивая инициализация MongoDB"""
        if self.mongo_db is None:
            self.mongo_db = await get_mongo_db()
        return self.mongo_db
    
    async def _get_user_info(self, keycloak_id: str) -> Dict[str, str]:
        """Получение информации о пользователе из user-service"""
        user_data = await self.user_client.get_user_by_keycloak_id(keycloak_id)
        if user_data:
            return {
                "username": user_data.get("username", keycloak_id),
                "keycloak_id": keycloak_id
            }
        # Fallback если user-service недоступен — используем keycloak_id как username
        # Это позволит системе работать даже при недоступности user-service
        logger.warning(f"Using fallback for user {keycloak_id}: user-service unavailable")
        return {
            "username": keycloak_id,
            "keycloak_id": keycloak_id
        }
    
    async def _check_chat_permission(self, chat_id: uuid.UUID, keycloak_id: str) -> Chat:
        """Проверка доступа пользователя к чату"""
        stmt = (
            select(Chat)
            .options(selectinload(Chat.participants))
            .where(Chat.id == chat_id)
        )
        result = await self.db.execute(stmt)
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise ChatNotFoundException(f"Chat {chat_id} not found")
        
        if chat.status == ChatStatus.BLOCKED:
            raise PermissionDeniedException("Chat is blocked")
        
        # Проверяем, является ли пользователь участником чата
        is_participant = any(
            p.keycloak_id == keycloak_id and p.left_at is None
            for p in chat.participants
        )
        
        if not is_participant:
            raise PermissionDeniedException("You are not a participant of this chat")
        
        return chat
    
    async def create_chat(self, chat_data: ChatCreate, creator_keycloak_id: str, creator_username: str) -> ChatResponse:
        """Создание нового чата"""
        try:
            # Проверяем валидность данных
            if chat_data.type == ChatType.DIRECT and len(chat_data.participant_ids) != 1:
                raise ValidationException("Direct chat must have exactly one other participant")
            
            if chat_data.type == ChatType.GROUP and len(chat_data.participant_ids) < 1:
                raise ValidationException("Group chat must have at least one other participant")
            
            # Проверяем, не существует ли уже такой же чат
            if chat_data.type == ChatType.DIRECT:
                # Для direct чата проверяем существующий чат между пользователями
                other_user_id = chat_data.participant_ids[0]
                
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
                existing_chat = result.scalar_one_or_none()
                
                if existing_chat:
                    # Возвращаем существующий чат
                    return await self._format_chat_response(existing_chat, creator_keycloak_id)
            
            # Получаем информацию о всех участниках из user-service
            # Создатель
            creator_info = {
                "keycloak_id": creator_keycloak_id,
                "username": creator_username
            }
            
            # Другие участники
            participants_info = [creator_info]
            for participant_id in chat_data.participant_ids:
                if participant_id != creator_keycloak_id:
                    user_info = await self._get_user_info(participant_id)
                    participants_info.append({
                        "keycloak_id": participant_id,
                        "username": user_info["username"]
                    })
            
            # Создаем новый чат
            new_chat = Chat(
                id=uuid.uuid4(),
                type=chat_data.type,
                name=chat_data.name,
                description=chat_data.description
            )
            
            self.db.add(new_chat)
            
            # Добавляем всех участников
            for p_info in participants_info:
                is_admin = (p_info["keycloak_id"] == creator_keycloak_id)
                participant = ChatParticipant(
                    chat_id=new_chat.id,
                    keycloak_id=p_info["keycloak_id"],
                    username=p_info["username"],
                    is_admin=is_admin
                )
                self.db.add(participant)
            
            await self.db.commit()
            await self.db.refresh(new_chat)
            
            logger.info(f"Chat created: {new_chat.id} by {creator_keycloak_id}")
            
            # Отправляем событие о создании чата
            await self._notify_chat_event(
                new_chat.id,
                "chat_created",
                {"chat_id": str(new_chat.id), "creator_id": creator_keycloak_id}
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
            # Основной запрос для получения чатов пользователя
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
            
            # Получаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()
            
            # Получаем чаты с сортировкой по последнему сообщению
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
            
            # Форматируем ответы
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
        
        # Проверяем права на обновление
        if chat.type == ChatType.DIRECT:
            raise PermissionDeniedException("Cannot update direct chat")
        
        # Проверяем, является ли пользователь администратором
        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )
        
        if not is_admin:
            raise PermissionDeniedException("Only chat admins can update chat")
        
        try:
            # Обновляем поля
            update_data = chat_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(chat, field) and value is not None:
                    setattr(chat, field, value)
            
            await self.db.commit()
            await self.db.refresh(chat)
            
            logger.info(f"Chat updated: {chat_id} by {keycloak_id}")
            
            # Отправляем событие об обновлении чата
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
        
        # Проверяем права на удаление
        if chat.type == ChatType.GROUP:
            is_admin = any(
                p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
                for p in chat.participants
            )
            if not is_admin:
                raise PermissionDeniedException("Only chat admins can delete group chat")
        
        try:
            # Получаем ID чата для события перед удалением
            chat_id_str = str(chat_id)
            
            # Удаляем все связанные сообщения из MongoDB (для полнотекстового поиска)
            try:
                mongo_db = await self._get_mongo_db()
                await mongo_db.messages.delete_many({"chat_id": chat_id_str})
                logger.debug(f"Deleted messages from MongoDB for chat {chat_id_str}")
            except Exception as e:
                logger.warning(f"Failed to delete messages from MongoDB: {e}")
                # Продолжаем даже если MongoDB недоступна
            
            # Каскадное удаление чата (SQLAlchemy удалит participants и messages из PostgreSQL
            # благодаря cascade="all, delete-orphan" в моделях)
            await self.db.delete(chat)
            await self.db.commit()
            
            logger.info(f"Chat deleted permanently: {chat_id_str} by {keycloak_id}")
            
            # Отправляем событие об удалении чата
            await self._notify_chat_event(
                chat_id,  # Важно: отправляем событие ДО коммита или используем ID из переменной
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
        # Проверяем rate limiting
        if not await websocket_manager.check_rate_limit(sender_keycloak_id):
            raise RateLimitException("Message rate limit exceeded")
        
        # Проверяем доступ к чату
        chat = await self._check_chat_permission(chat_id, sender_keycloak_id)
        
        try:
            # Создаем сообщение
            new_message = Message(
                id=uuid.uuid4(),
                chat_id=chat_id,
                sender_keycloak_id=sender_keycloak_id,
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
            
            # Обновляем время последнего обновления чата
            chat.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(new_message)
            
            logger.info(f"Message sent: {new_message.id} in chat {chat_id}")
            
            # Форматируем ответ
            message_response = MessageResponse(
                id=new_message.id,
                chat_id=new_message.chat_id,
                sender_keycloak_id=new_message.sender_keycloak_id,
                sender_username=new_message.sender_username,
                content=new_message.content,
                message_type=new_message.message_type,
                status=new_message.status,
                reply_to_id=new_message.reply_to_id,
                media_url=new_message.media_url,
                media_type=new_message.media_type,
                file_size=new_message.file_size,
                created_at=new_message.created_at,
                updated_at=new_message.updated_at
            )
            
            # Отправляем сообщение через WebSocket
            ws_message = {
                "type": "message",
                "chat_id": str(chat_id),
                "message": message_response.model_dump(),
                "sender_id": sender_keycloak_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket_manager.broadcast_to_chat(
                ws_message,
                str(chat_id),
                exclude_user=sender_keycloak_id
            )
            
            # Сохраняем в MongoDB для полнотекстового поиска
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
        """Получение сообщений из чата"""
        await self._check_chat_permission(chat_id, keycloak_id)
        
        try:
            # Основной запрос для сообщений
            query = (
                select(Message)
                .where(Message.chat_id == chat_id)
            )
            
            if before:
                query = query.where(Message.created_at < before)
            
            # Получаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()
            
            # Получаем сообщения с пагинацией
            query = (
                query
                .order_by(desc(Message.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            # Обновляем статус прочтения для полученных сообщений
            if messages:
                message_ids = [msg.id for msg in messages if msg.sender_keycloak_id != keycloak_id]
                if message_ids:
                    await self._mark_messages_as_read(chat_id, keycloak_id, message_ids)
            
            # Форматируем ответы
            message_responses = []
            for message in reversed(messages):  # Восстанавливаем правильный порядок
                message_response = MessageResponse(
                    id=message.id,
                    chat_id=message.chat_id,
                    sender_keycloak_id=message.sender_keycloak_id,
                    sender_username=message.sender_username,
                    content=message.content,
                    message_type=message.message_type,
                    status=message.status,
                    reply_to_id=message.reply_to_id,
                    media_url=message.media_url,
                    media_type=message.media_type,
                    file_size=message.file_size,
                    created_at=message.created_at,
                    updated_at=message.updated_at
                )
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
            
            # Проверяем права на удаление
            chat = await self._check_chat_permission(message.chat_id, keycloak_id)
            
            is_sender = message.sender_keycloak_id == keycloak_id
            is_admin = any(
                p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
                for p in chat.participants
            )
            
            if not (is_sender or is_admin):
                raise PermissionDeniedException("Cannot delete this message")
            
            # Удаляем сообщение
            await self.db.delete(message)
            await self.db.commit()
            
            logger.info(f"Message deleted: {message_id} by {keycloak_id}")
            
            # Отправляем событие об удалении сообщения
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
    
    async def mark_messages_as_read(self, chat_id: uuid.UUID, keycloak_id: str, message_ids: List[uuid.UUID]) -> bool:
        """Отметка сообщений как прочитанных"""
        await self._check_chat_permission(chat_id, keycloak_id)
        
        try:
            # Обновляем статус сообщений
            stmt = (
                update(Message)
                .where(
                    Message.id.in_(message_ids),
                    Message.chat_id == chat_id,
                    Message.sender_keycloak_id != keycloak_id,
                    Message.status != MessageStatus.READ
                )
                .values(status=MessageStatus.READ)
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"{result.rowcount} messages marked as read in chat {chat_id}")
                
                # Отправляем подтверждения прочтения через WebSocket
                for message_id in message_ids:
                    await websocket_manager.send_read_receipt(chat_id, keycloak_id, message_id)
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking messages as read: {e}")
            raise DatabaseException("Failed to mark messages as read")
    
    async def add_participant(self, chat_id: uuid.UUID, keycloak_id: str, new_user_id: str) -> bool:
        """Добавление участника в чат"""
        chat = await self._check_chat_permission(chat_id, keycloak_id)
        
        if chat.type != ChatType.GROUP:
            raise ValidationException("Cannot add participants to non-group chat")
        
        # Проверяем права на добавление участников
        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )
        
        if not is_admin:
            raise PermissionDeniedException("Only chat admins can add participants")
        
        try:
            # Проверяем, не является ли пользователь уже участником
            existing_participant = any(
                p.keycloak_id == new_user_id and p.left_at is None
                for p in chat.participants
            )
            
            if existing_participant:
                raise ValidationException("User is already a participant")
            
            # Получаем информацию о новом участнике из user-service
            user_info = await self._get_user_info(new_user_id)
            
            # Добавляем участника
            new_participant = ChatParticipant(
                chat_id=chat_id,
                keycloak_id=new_user_id,
                username=user_info["username"],
                is_admin=False
            )
            
            self.db.add(new_participant)
            await self.db.commit()
            
            logger.info(f"User {new_user_id} added to chat {chat_id}")
            
            # Отправляем событие о добавлении участника
            await self._notify_chat_event(
                chat_id,
                "user_joined",
                {"chat_id": str(chat_id), "user_id": new_user_id, "added_by": keycloak_id}
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
        
        # Проверяем права
        is_admin = any(
            p.keycloak_id == keycloak_id and p.is_admin and p.left_at is None
            for p in chat.participants
        )
        
        is_self = user_to_remove_id == keycloak_id
        
        if not (is_admin or is_self):
            raise PermissionDeniedException("Cannot remove this participant")
        
        try:
            # Находим участника
            stmt = select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.keycloak_id == user_to_remove_id,
                ChatParticipant.left_at.is_(None)
            )
            result = await self.db.execute(stmt)
            participant = result.scalar_one_or_none()
            
            if not participant:
                raise ValidationException("Participant not found")
            
            # Отмечаем время выхода
            participant.left_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"User {user_to_remove_id} removed from chat {chat_id}")
            
            # Отправляем событие о выходе участника
            await self._notify_chat_event(
                chat_id,
                "user_left",
                {"chat_id": str(chat_id), "user_id": user_to_remove_id, "removed_by": keycloak_id}
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
            # Для поиска используем MongoDB
            mongo_db = await self._get_mongo_db()
            collection = mongo_db.messages
            
            # Строим фильтр поиска
            search_filter = {"content": {"$regex": query, "$options": "i"}}
            
            if chat_id:
                # Проверяем доступ к чату
                await self._check_chat_permission(chat_id, keycloak_id)
                search_filter["chat_id"] = str(chat_id)
            else:
                # Получаем все чаты пользователя
                user_chats = await self._get_user_chat_ids(keycloak_id)
                search_filter["chat_id"] = {"$in": user_chats}
            
            # Выполняем поиск
            cursor = collection.find(search_filter)
            cursor.sort("created_at", -1)
            cursor.skip(skip).limit(limit)
            
            mongo_messages = await cursor.to_list(length=limit)
            
            # Получаем полные данные из PostgreSQL
            message_responses = []
            for msg in mongo_messages:
                stmt = select(Message).where(Message.id == uuid.UUID(msg["message_id"]))
                result = await self.db.execute(stmt)
                message = result.scalar_one_or_none()
                
                if message:
                    message_response = MessageResponse(
                        id=message.id,
                        chat_id=message.chat_id,
                        sender_keycloak_id=message.sender_keycloak_id,
                        sender_username=message.sender_username,
                        content=message.content,
                        message_type=message.message_type,
                        status=message.status,
                        reply_to_id=message.reply_to_id,
                        media_url=message.media_url,
                        media_type=message.media_type,
                        file_size=message.file_size,
                        created_at=message.created_at,
                        updated_at=message.updated_at
                    )
                    message_responses.append(message_response)
            
            return message_responses
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise DatabaseException("Failed to search messages")
    
    async def _format_chat_response(self, chat: Chat, keycloak_id: str) -> ChatResponse:
        """Форматирование ответа чата"""
        # Получаем последнее сообщение
        stmt = (
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_message = result.scalar_one_or_none()
        
        # Получаем количество непрочитанных сообщений
        unread_stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.chat_id == chat.id,
                Message.sender_keycloak_id != keycloak_id,
                Message.status != MessageStatus.READ
            )
        )
        unread_result = await self.db.execute(unread_stmt)
        unread_count = unread_result.scalar_one()
        
        # Форматируем последнее сообщение
        last_message_data = None
        if last_message:
            last_message_data = {
                "id": str(last_message.id),
                "content": last_message.content,
                "sender_id": last_message.sender_keycloak_id,
                "sender_name": last_message.sender_username,
                "created_at": last_message.created_at.isoformat(),
                "type": last_message.message_type
            }
        
        # Форматируем участников
        participants = []
        for participant in chat.participants:
            if participant.left_at is None:
                participants.append({
                    "keycloak_id": participant.keycloak_id,
                    "username": participant.username,
                    "is_admin": participant.is_admin,
                    "notifications_enabled": participant.notifications_enabled
                })
        
        return ChatResponse(
            id=chat.id,
            type=chat.type,
            status=chat.status,
            name=chat.name,
            description=chat.description,
            avatar_url=chat.avatar_url,
            participants=participants,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            last_message=last_message_data,
            unread_count=unread_count
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
            "event": event.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_to_chat(ws_message, str(chat_id))
    
    async def _mark_messages_as_read(self, chat_id: uuid.UUID, keycloak_id: str, message_ids: List[uuid.UUID]):
        """Внутренний метод для отметки сообщений как прочитанных"""
        if not message_ids:
            return
        
        try:
            stmt = (
                update(Message)
                .where(
                    Message.id.in_(message_ids),
                    Message.chat_id == chat_id,
                    Message.sender_keycloak_id != keycloak_id
                )
                .values(status=MessageStatus.READ)
            )
            
            await self.db.execute(stmt)
            
        except Exception as e:
            logger.error(f"Error marking messages as read internally: {e}")
    
    async def _save_message_to_mongo(self, message: MessageResponse):
        """Сохранение сообщения в MongoDB для поиска"""
        try:
            mongo_db = await self._get_mongo_db()
            collection = mongo_db.messages
            
            mongo_doc = {
                "message_id": str(message.id),
                "chat_id": str(message.chat_id),
                "sender_id": message.sender_keycloak_id,
                "sender_name": message.sender_username,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at,
                "updated_at": message.updated_at
            }
            
            await collection.insert_one(mongo_doc)
            
        except Exception as e:
            logger.error(f"Error saving message to MongoDB: {e}")
    
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