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
    keycloak_id: str
    display_name: str
    username: Optional[str] = None
    is_admin: bool = False
    notifications_enabled: bool = True
    avatar_url: Optional[str] = None

class ChatCreate(BaseModel):
    type: ChatType = ChatType.DIRECT
    participant_ids: List[str] = Field(..., min_items=1)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None

class ChatUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    status: Optional[ChatStatus] = None

class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    type: ChatType
    status: ChatStatus
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    participants: List[ParticipantBase]
    created_at: datetime
    updated_at: datetime
    last_message: Optional[Dict[str, Any]] = None
    unread_count: int = 0

class ChatListResponse(BaseModel):
    chats: List[ChatResponse]
    total: int
    page: int
    size: int

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field("text", pattern="^(text|image|file|audio|video)$")
    reply_to_id: Optional[uuid.UUID] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    file_size: Optional[int] = Field(None, ge=0)

class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_keycloak_id: str
    sender_display_name: str
    sender_username: Optional[str] = None
    content: str
    message_type: str
    status: MessageStatus
    is_edited: bool = False  # Уже есть
    reply_to_id: Optional[uuid.UUID] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Поля для статуса прочтения
    read_by: List[str] = Field(default_factory=list, description="Список пользователей, прочитавших сообщение")
    read_count: int = Field(0, description="Количество пользователей, прочитавших сообщение")
    is_read_by_me: bool = Field(False, description="Прочитал ли текущий пользователь")

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    size: int

class MessageIdsRequest(BaseModel):
    message_ids: List[uuid.UUID] = Field(..., min_items=1)

class SearchMessagesResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    query: str

class OnlineUsersResponse(BaseModel):
    online_users: List[str]
    count: int

# WebSocket модели
class WebSocketMessage(BaseModel):
    type: str = Field(..., pattern="^(message|typing|read_receipt|chat_update|error|connection_established|subscribed|ping|pong|message_updated|message_deleted)$")
    chat_id: Optional[uuid.UUID] = None
    message: Optional[Dict[str, Any]] = None
    sender_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TypingIndicator(BaseModel):
    chat_id: uuid.UUID
    user_id: str
    display_name: str
    is_typing: bool

class ReadReceipt(BaseModel):
    chat_id: uuid.UUID
    user_id: str
    message_id: uuid.UUID
    read_at: datetime
    # Добавляем для массовых уведомлений
    message_ids: Optional[List[uuid.UUID]] = None

class ChatEvent(BaseModel):
    event_type: str = Field(..., pattern="^(chat_created|chat_updated|chat_deleted|user_joined|user_left)$")
    chat_id: uuid.UUID
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Новая схема для запроса статуса прочтения
class MessageReadStatusResponse(BaseModel):
    """Ответ с информацией о том, кто прочитал сообщение"""
    model_config = ConfigDict(from_attributes=True)
    
    message_id: uuid.UUID
    read_by_users: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Список пользователей с временем прочтения"
    )
    total_read_count: int
    
    
class BulkReadReceiptRequest(BaseModel):
    """Запрос на отметку нескольких сообщений как прочитанных"""
    message_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)