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
    participant_ids: List[str] = Field(..., min_items=1)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

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
    name: Optional[str]
    description: Optional[str]
    avatar_url: Optional[str]
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
    file_size: Optional[int] = Field(None)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_keycloak_id: str
    sender_username: str
    content: str
    message_type: str
    status: MessageStatus
    reply_to_id: Optional[uuid.UUID]
    media_url: Optional[str]
    media_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    size: int

# ИСПРАВЛЕНО: Расширенный список типов для WebSocket
class WebSocketMessage(BaseModel):
    type: str = Field(..., pattern="^(message|typing|read_receipt|chat_update|error|connection_established|subscribed|ping|pong)$")
    chat_id: Optional[uuid.UUID] = None
    message: Optional[Dict[str, Any]] = None
    sender_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TypingIndicator(BaseModel):
    chat_id: uuid.UUID
    user_id: str
    username: str
    is_typing: bool

class ReadReceipt(BaseModel):
    chat_id: uuid.UUID
    user_id: str
    message_id: uuid.UUID
    read_at: datetime

class ChatEvent(BaseModel):
    event_type: str = Field(..., pattern="^(chat_created|chat_updated|chat_deleted|user_joined|user_left)$")
    chat_id: uuid.UUID
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)