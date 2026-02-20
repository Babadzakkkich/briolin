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
    """Участник чата с отображаемым именем из profile-service"""
    keycloak_id: str
    display_name: str = Field(..., description="Имя и фамилия пользователя (first_name + last_name)")
    username: Optional[str] = Field(None, description="Username для совместимости")
    is_admin: bool = False
    notifications_enabled: bool = True
    avatar_url: Optional[str] = Field(None, description="URL аватарки пользователя")

class ChatCreate(BaseModel):
    """
    Создание нового чата.
    
    Для личного чата (type=direct):
    - Название и аватарка генерируются автоматически из профиля собеседника
    - Должен быть указан ровно один participant_id
    
    Для группового чата (type=group):
    - Название и аватарка задаются создателем
    """
    type: ChatType = ChatType.DIRECT
    participant_ids: List[str] = Field(
        ..., 
        min_items=1, 
        description="Список Keycloak ID участников"
    )
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100, 
        description="Название чата (только для групповых чатов, для личных игнорируется)"
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Описание чата (только для групповых чатов)"
    )
    avatar_url: Optional[str] = Field(
        None, 
        description="URL аватарки чата (только для групповых чатов, для личных игнорируется)"
    )

class ChatUpdate(BaseModel):
    """Обновление информации о чате (только для групповых чатов)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    status: Optional[ChatStatus] = None

class ChatResponse(BaseModel):
    """Ответ с информацией о чате с персонализированным названием"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    type: ChatType
    status: ChatStatus
    # Для direct чатов: имя и аватарка собеседника
    # Для group чатов: заданные создателем
    name: Optional[str] = Field(None, description="Название чата (персонализировано для каждого пользователя в direct)")
    description: Optional[str] = None
    avatar_url: Optional[str] = Field(None, description="URL аватарки чата (персонализирован для direct)")
    participants: List[ParticipantBase]
    created_at: datetime
    updated_at: datetime
    last_message: Optional[Dict[str, Any]] = Field(None, description="Последнее сообщение в чате")
    unread_count: int = Field(0, description="Количество непрочитанных сообщений")

class ChatListResponse(BaseModel):
    """Список чатов с пагинацией"""
    chats: List[ChatResponse]
    total: int
    page: int
    size: int

class MessageCreate(BaseModel):
    """Создание нового сообщения"""
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field("text", pattern="^(text|image|file|audio|video)$")
    reply_to_id: Optional[uuid.UUID] = Field(None, description="ID сообщения, на которое отвечаем")
    media_url: Optional[str] = Field(None, description="URL медиа-файла")
    media_type: Optional[str] = Field(None, description="Тип медиа")
    file_size: Optional[int] = Field(None, ge=0, description="Размер файла в байтах")

class MessageUpdate(BaseModel):
    """Редактирование существующего сообщения"""
    content: str = Field(..., min_length=1, max_length=5000, description="Новый текст сообщения")

class MessageResponse(BaseModel):
    """Ответ с сообщением с отображаемым именем отправителя"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_keycloak_id: str
    sender_display_name: str = Field(..., description="Имя и фамилия отправителя (first_name + last_name)")
    sender_username: Optional[str] = Field(None, description="Username отправителя (для совместимости)")
    content: str
    message_type: str
    status: MessageStatus
    is_edited: bool = Field(default=False, description="Было ли сообщение отредактировано")
    reply_to_id: Optional[uuid.UUID] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # === НОВЫЕ ПОЛЯ для статуса прочтения ===
    read_by: List[str] = Field(
        default_factory=list, 
        description="Список пользователей, прочитавших сообщение"
    )
    read_count: int = Field(
        0, 
        description="Количество пользователей, прочитавших сообщение"
    )
    is_read_by_me: bool = Field(
        False, 
        description="Прочитал ли текущий пользователь"
    )

class MessageListResponse(BaseModel):
    """Список сообщений с пагинацией"""
    messages: List[MessageResponse]
    total: int
    page: int
    size: int

class MessageIdsRequest(BaseModel):
    """Запрос на отметку сообщений как прочитанных"""
    message_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100, description="Список ID сообщений")

# === НОВАЯ СХЕМА: массовая отметка сообщений ===
class BulkMessageIdsRequest(BaseModel):
    """Запрос на массовую отметку сообщений как прочитанных"""
    message_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=500, description="Список ID сообщений")

# === НОВАЯ СХЕМА: информация о прочитавших сообщение ===
class ReadByUserInfo(BaseModel):
    """Информация о пользователе, прочитавшем сообщение"""
    keycloak_id: str
    display_name: str
    avatar_url: Optional[str] = None
    read_at: datetime

class MessageReadStatusResponse(BaseModel):
    """Ответ с информацией о том, кто прочитал сообщение"""
    message_id: uuid.UUID
    read_by_users: List[ReadByUserInfo] = Field(
        default_factory=list,
        description="Список пользователей с временем прочтения"
    )
    total_read_count: int

class SearchMessagesResponse(BaseModel):
    """Результат поиска сообщений"""
    messages: List[MessageResponse]
    total: int
    query: str

class OnlineUsersResponse(BaseModel):
    """Список онлайн пользователей"""
    online_users: List[str]
    count: int

# WebSocket модели для документации
class TypingIndicator(BaseModel):
    """Индикатор набора текста"""
    chat_id: uuid.UUID
    user_id: str
    display_name: str = Field(..., description="Имя и фамилия пользователя")
    is_typing: bool

class ReadReceipt(BaseModel):
    """Подтверждение прочтения одного сообщения"""
    chat_id: uuid.UUID
    user_id: str
    message_id: uuid.UUID
    read_at: datetime

# === НОВАЯ WebSocket модель: массовое подтверждение прочтения ===
class BulkReadReceipt(BaseModel):
    """Массовое подтверждение прочтения нескольких сообщений"""
    type: str = "bulk_read_receipt"
    chat_id: uuid.UUID
    user_id: str
    message_ids: List[uuid.UUID]
    read_at: datetime

class WebSocketMessage(BaseModel):
    """WebSocket сообщение"""
    type: str = Field(..., pattern="^(message|typing|read_receipt|bulk_read_receipt|chat_update|error|connection_established|subscribed|ping|pong|message_updated|message_deleted)$")
    chat_id: Optional[uuid.UUID] = None
    message: Optional[Dict[str, Any]] = None
    sender_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)