from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    """Типы событий в системе"""
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_STATUS_CHANGED = "user.status_changed"
    USER_ROLES_UPDATED = "user.roles_updated"
    USER_PROFILE_CREATED = "user.profile_created"
    USER_PROFILE_UPDATED = "user.profile_updated"

class BaseEvent(BaseModel):
    """Базовый класс для всех событий"""
    event_type: str
    event_id: str = Field(..., description="Уникальный ID события")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = Field(..., description="Сервис-источник события")
    version: str = "1.0"
    correlation_id: Optional[str] = Field(None, description="ID для отслеживания цепочки событий")
    user_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)