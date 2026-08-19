from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"

class ChatStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class ParticipantBase(BaseModel):
    """Базовая схема данных участника чата."""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    username: Optional[str] = Field(None, description='Имя пользователя участника чата')
    is_admin: bool = Field(False, description='Признак наличия административных прав в чате')
    notifications_enabled: bool = Field(True, description='Признак включённых уведомлений для участника чата')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')

class ChatCreate(BaseModel):
    """Схема данных для создания нового личного или группового чата."""
    type: ChatType = Field(ChatType.DIRECT, description='Тип создаваемого чата')
    participant_ids: List[str] = Field(..., min_items=1, description='Список Keycloak ID участников создаваемого чата')
    name: Optional[str] = Field(None, min_length=1, max_length=100, description='Название чата')
    description: Optional[str] = Field(None, max_length=500, description='Описание чата')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')

class ChatUpdate(BaseModel):
    """Схема данных для изменения настроек и информации существующего чата."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description='Новое название чата')
    description: Optional[str] = Field(None, max_length=500, description='Новое описание чата')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')
    status: Optional[ChatStatus] = Field(None, description='Новый статус чата')

class ChatResponse(BaseModel):
    """Схема ответа с полной информацией о чате и его текущем состоянии."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description='Уникальный идентификатор чата')
    type: ChatType = Field(..., description='Тип чата')
    status: ChatStatus = Field(..., description='Текущий статус чата')
    name: Optional[str] = Field(None, description='Название чата')
    description: Optional[str] = Field(None, description='Описание чата')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')
    participants: List[ParticipantBase] = Field(..., description='Список участников чата')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления записи')
    last_message: Optional[Dict[str, Any]] = Field(None, description='Данные последнего сообщения в чате')
    unread_count: int = Field(0, description='Количество непрочитанных сообщений в чате')
    match_id: Optional[int] = Field(None, description='Уникальный идентификатор совпадения пользователей')

class ChatListResponse(BaseModel):
    """Схема ответа со списком доступных пользователю чатов и пагинацией."""
    chats: List[ChatResponse] = Field(..., description='Список чатов пользователя')
    total: int = Field(..., description='Общее количество элементов')
    page: int = Field(..., description='Номер страницы результатов')
    size: int = Field(..., description='Количество элементов на странице')

class MessageCreate(BaseModel):
    """Схема данных для отправки нового сообщения в чат."""
    content: str = Field(..., min_length=1, max_length=5000, description='Текст сообщения')
    message_type: str = Field('text', pattern='^(text|image|file|audio|video)$', description='Тип сообщения')
    reply_to_id: Optional[uuid.UUID] = Field(None, description='Идентификатор сообщения, на которое отправляется ответ')
    media_url: Optional[str] = Field(None, description='URL медиафайла сообщения')
    media_type: Optional[str] = Field(None, description='Тип медиафайла сообщения')
    file_size: Optional[int] = Field(None, ge=0, description='Размер файла в байтах')

class MessageUpdate(BaseModel):
    """Схема данных для редактирования существующего сообщения."""
    content: str = Field(..., min_length=1, max_length=5000, description='Текст сообщения')

class MessageResponse(BaseModel):
    """Схема ответа с полной информацией о сообщении чата."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description='Уникальный идентификатор сообщения')
    chat_id: uuid.UUID = Field(..., description='Уникальный идентификатор чата')
    sender_keycloak_id: str = Field(..., description='Keycloak ID отправителя сообщения')
    sender_display_name: str = Field(..., description='Отображаемое имя отправителя сообщения')
    sender_username: Optional[str] = Field(None, description='Имя пользователя отправителя сообщения')
    content: str = Field(..., description='Текст сообщения')
    message_type: str = Field(..., description='Тип сообщения')
    status: MessageStatus = Field(..., description='Текущий статус сообщения')
    is_edited: bool = Field(False, description='Признак того, что сообщение было отредактировано')  # Уже есть
    reply_to_id: Optional[uuid.UUID] = Field(None, description='Идентификатор сообщения, на которое отправляется ответ')
    media_url: Optional[str] = Field(None, description='URL медиафайла сообщения')
    media_type: Optional[str] = Field(None, description='Тип медиафайла сообщения')
    file_size: Optional[int] = Field(None, description='Размер файла в байтах')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления записи')
    
    # Поля для статуса прочтения
    read_by: List[str] = Field(default_factory=list, description='Список Keycloak ID пользователей, прочитавших сообщение')
    read_count: int = Field(0, description='Количество пользователей, прочитавших сообщение')
    is_read_by_me: bool = Field(False, description='Признак того, что текущий пользователь прочитал сообщение')

class MessageListResponse(BaseModel):
    """Схема ответа со списком сообщений выбранного чата и пагинацией."""
    messages: List[MessageResponse] = Field(..., description='Список сообщений')
    total: int = Field(..., description='Общее количество элементов')
    page: int = Field(..., description='Номер страницы результатов')
    size: int = Field(..., description='Количество элементов на странице')

class MessageIdsRequest(BaseModel):
    """Схема запроса со списком идентификаторов сообщений для групповой операции."""
    message_ids: List[uuid.UUID] = Field(..., min_items=1, description='Список идентификаторов сообщений')

class SearchMessagesResponse(BaseModel):
    """Схема ответа с результатами поиска сообщений по заданному запросу."""
    messages: List[MessageResponse] = Field(..., description='Список сообщений')
    total: int = Field(..., description='Общее количество элементов')
    query: str = Field(..., description='Поисковый запрос')

class OnlineUsersResponse(BaseModel):
    """Схема ответа со списком пользователей, находящихся онлайн."""
    online_users: List[str] = Field(..., description='Список Keycloak ID пользователей, находящихся онлайн')
    count: int = Field(..., description='Количество элементов')

# WebSocket модели
class WebSocketMessage(BaseModel):
    """Схема сообщения, передаваемого через WebSocket-соединение."""
    type: str = Field(..., pattern='^(message|typing|read_receipt|chat_update|error|connection_established|subscribed|ping|pong|message_updated|message_deleted)$', description='Тип WebSocket-события')
    chat_id: Optional[uuid.UUID] = Field(None, description='Уникальный идентификатор чата')
    message: Optional[Dict[str, Any]] = Field(None, description='Данные сообщения WebSocket-события')
    sender_id: Optional[str] = Field(None, description='Keycloak ID отправителя сообщения')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Дата и время события')

class TypingIndicator(BaseModel):
    """Схема события, сообщающего о наборе текста пользователем в чате."""
    chat_id: uuid.UUID = Field(..., description='Уникальный идентификатор чата')
    user_id: str = Field(..., description='Keycloak ID пользователя, изменившего статус набора текста')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    is_typing: bool = Field(..., description='Признак того, что пользователь в данный момент печатает сообщение')

class ReadReceipt(BaseModel):
    """Схема события, подтверждающего прочтение сообщения или набора сообщений."""
    chat_id: uuid.UUID = Field(..., description='Уникальный идентификатор чата')
    user_id: str = Field(..., description='Keycloak ID пользователя, прочитавшего сообщение')
    message_id: uuid.UUID = Field(..., description='Уникальный идентификатор сообщения')
    read_at: datetime = Field(..., description='Дата и время прочтения сообщения')
    message_ids: Optional[List[uuid.UUID]] = Field(None, description='Список идентификаторов сообщений')

class ChatEvent(BaseModel):
    """Схема внутреннего события, связанного с изменениями или действиями в чате."""
    event_type: str = Field(..., pattern='^(chat_created|chat_updated|chat_deleted|user_joined|user_left)$', description='Тип события')
    chat_id: uuid.UUID = Field(..., description='Уникальный идентификатор чата')
    data: Dict[str, Any] = Field(..., description='Полезная нагрузка события чата')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Дата и время события')


class MessageReadStatusResponse(BaseModel):
    """Ответ с информацией о том, кто прочитал сообщение"""
    model_config = ConfigDict(from_attributes=True)
    
    message_id: uuid.UUID = Field(..., description='Уникальный идентификатор сообщения')
    read_by_users: List[Dict[str, Any]] = Field(default_factory=list, description='Информация о пользователях, прочитавших сообщение')
    total_read_count: int = Field(..., description='Общее количество пользователей, прочитавших сообщение')
    
    
class BulkReadReceiptRequest(BaseModel):
    """Запрос на отметку нескольких сообщений как прочитанных"""
    message_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100, description='Список идентификаторов сообщений')