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
    READ = "read"
    FAILED = "failed"

class ParticipantBase(BaseModel):
    keycloak_id: str
    username: str
    is_admin: bool = False
    notifications_enabled: bool = True

class ChatCreate(BaseModel):
    type: ChatType = ChatType.DIRECT
    participant_ids: List[str] = Field(..., min_items=1, description="List of participant Keycloak IDs")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Chat name (for group chats)")
    description: Optional[str] = Field(None, max_length=500, description="Chat description (for group chats)")

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
    reply_to_id: Optional[uuid.UUID] = Field(None)
    media_url: Optional[str] = Field(None)
    media_type: Optional[str] = Field(None)
    file_size: Optional[int] = Field(None, ge=0)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_keycloak_id: str
    sender_username: str
    content: str
    message_type: str
    status: MessageStatus
    reply_to_id: Optional[uuid.UUID] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    size: int

class MessageIdsRequest(BaseModel):
    """Модель для запроса на отметку сообщений как прочитанных"""
    message_ids: List[uuid.UUID] = Field(..., min_items=1)

class SearchMessagesResponse(BaseModel):
    """Модель ответа для поиска сообщений"""
    messages: List[MessageResponse]
    total: int
    query: str

class OnlineUsersResponse(BaseModel):
    """Модель ответа для получения онлайн пользователей"""
    online_users: List[str]
    count: int