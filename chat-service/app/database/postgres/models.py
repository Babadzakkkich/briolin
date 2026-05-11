import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Base(DeclarativeBase):
    pass

class ChatType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"

class ChatStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), default=ChatType.DIRECT)
    status: Mapped[ChatStatus] = mapped_column(Enum(ChatStatus), default=ChatStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    direct_chat_partner_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    
    participants: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    
    __table_args__ = (
        Index('idx_chats_updated_at', 'updated_at'),
        Index('idx_chats_status', 'status'),
    )

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete='CASCADE'))
    keycloak_id: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")
    
    __table_args__ = (
        Index('idx_chat_participants_user', 'keycloak_id', 'chat_id'),
        Index('idx_chat_participants_chat', 'chat_id', 'keycloak_id'),
    )

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete='CASCADE'))
    sender_keycloak_id: Mapped[str] = mapped_column(String, index=True)
    sender_display_name: Mapped[str] = mapped_column(String)
    sender_username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String, default="text")
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), default=MessageStatus.SENT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    
    # Связь со статусами прочтения
    read_statuses: Mapped[List["MessageReadStatus"]] = relationship(
        "MessageReadStatus",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    
    __table_args__ = (
        Index('idx_messages_chat_created', 'chat_id', 'created_at'),
        Index('idx_messages_sender', 'sender_keycloak_id', 'created_at'),
    )
    
    def is_read_by(self, keycloak_id: str) -> bool:
        """Проверяет, прочитал ли конкретный пользователь сообщение"""
        return any(rs.keycloak_id == keycloak_id for rs in self.read_statuses)
    
    @property
    def read_by_count(self) -> int:
        """Количество пользователей, прочитавших сообщение"""
        return len(self.read_statuses)
    
    @property
    def read_by_users(self) -> List[str]:
        """Список пользователей, прочитавших сообщение"""
        return [rs.keycloak_id for rs in self.read_statuses]


class MessageReadStatus(Base):
    """
    Таблица для отслеживания, кто из пользователей прочитал сообщение.
    Позволяет каждому участнику чата иметь свой статус прочтения.
    """
    __tablename__ = "message_read_status"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("messages.id", ondelete='CASCADE')
    )
    keycloak_id: Mapped[str] = mapped_column(String, index=True)  # Кто прочитал
    read_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь с сообщением
    message: Mapped["Message"] = relationship("Message", back_populates="read_statuses")
    
    __table_args__ = (
        # Уникальность: одно сообщение - один пользователь - одна запись
        UniqueConstraint('message_id', 'keycloak_id', name='uq_message_read_user'),
        Index('idx_message_read_status_message', 'message_id'),
        Index('idx_message_read_status_user', 'keycloak_id'),
        Index('idx_message_read_status_message_user', 'message_id', 'keycloak_id'),
    )