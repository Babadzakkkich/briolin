from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    """Типы событий в системе"""
    # События регистрации и создания
    USER_REGISTERED = "user.registered"
    USER_PROFILE_CREATED = "user.profile_created"
    
    # События обновления (разделены по ответственности)
    USER_PROFILE_UPDATE_REQUESTED = "user.profile_update_requested"
    USER_PROFILE_UPDATED = "user.profile_updated"
    
    # События аватарок
    AVATAR_UPLOADED = "avatar.uploaded"
    AVATAR_DELETED = "avatar.deleted"
    
    # События статуса
    USER_STATUS_CHANGE_REQUESTED = "user.status_change_requested"
    USER_STATUS_CHANGED = "user.status_changed"
    
    # === НОВЫЕ СОБЫТИЯ ОНЛАЙН-СТАТУСА ===
    USER_ONLINE = "user.online"
    USER_OFFLINE = "user.offline"
    USER_HEARTBEAT = "user.heartbeat"
    
    # События ролей
    USER_ROLES_UPDATE_REQUESTED = "user.roles_update_requested"
    USER_ROLES_UPDATED = "user.roles_updated"
    
    # События удаления
    USER_DELETION_REQUESTED = "user.deletion_requested"
    USER_DELETED = "user.deleted"
    
    TEST_STARTED = "test.started"
    TEST_COMPLETED = "test.completed"
    TEST_RESULTS_UPDATED = "test.results_updated"
    
    # События чатов
    CHAT_CREATED = "chat.created"
    CHAT_UPDATED = "chat.updated"
    CHAT_DELETED = "chat.deleted"
    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_READ = "message.read"
    USER_TYPING = "user.typing"
    USER_ONLINE_CHAT = "user.online"  # Alias для обратной совместимости
    USER_OFFLINE_CHAT = "user.offline"  # Alias для обратной совместимости

class BaseEvent(BaseModel):
    """Базовый класс для всех событий"""
    event_type: EventType
    event_id: str = Field(..., description="Уникальный ID события")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = Field(..., description="Сервис-источник события")
    version: str = "1.0"
    correlation_id: str = Field(..., description="ID для отслеживания цепочки событий")
    user_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed_by: List[str] = Field(default_factory=list, description="Сервисы, уже обработавшие это событие")
    
    def is_processed_by(self, service_name: str) -> bool:
        """Проверяет, обработал ли событие указанный сервис"""
        return service_name in self.processed_by
    
    def mark_as_processed(self, service_name: str) -> None:
        """Помечает событие как обработанное сервисом"""
        if service_name not in self.processed_by:
            self.processed_by.append(service_name)


class UserOnlineEvent(BaseModel):
    """Событие: пользователь подключился (онлайн)"""
    event_type: EventType = EventType.USER_ONLINE
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = "chat-service"
    keycloak_id: str
    connection_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_base_event(self) -> BaseEvent:
        return BaseEvent(
            event_type=self.event_type,
            event_id=self.event_id,
            timestamp=self.timestamp,
            source_service=self.source_service,
            correlation_id=self.event_id,
            user_data={
                "keycloak_id": self.keycloak_id,
                "connection_id": self.connection_id
            },
            metadata=self.metadata
        )


class UserOfflineEvent(BaseModel):
    """Событие: пользователь отключился (офлайн)"""
    event_type: EventType = EventType.USER_OFFLINE
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = "chat-service"
    keycloak_id: str
    connection_id: Optional[str] = None
    reason: Optional[str] = None  # disconnect, timeout, cleanup
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_base_event(self) -> BaseEvent:
        return BaseEvent(
            event_type=self.event_type,
            event_id=self.event_id,
            timestamp=self.timestamp,
            source_service=self.source_service,
            correlation_id=self.event_id,
            user_data={
                "keycloak_id": self.keycloak_id,
                "connection_id": self.connection_id,
                "reason": self.reason
            },
            metadata=self.metadata
        )


class UserHeartbeatEvent(BaseModel):
    """Событие: периодическое подтверждение активности пользователя"""
    event_type: EventType = EventType.USER_HEARTBEAT
    event_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = "chat-service"
    keycloak_id: str
    connection_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_base_event(self) -> BaseEvent:
        return BaseEvent(
            event_type=self.event_type,
            event_id=self.event_id,
            timestamp=self.timestamp,
            source_service=self.source_service,
            correlation_id=self.event_id,
            user_data={
                "keycloak_id": self.keycloak_id,
                "connection_id": self.connection_id
            },
            metadata=self.metadata
        )