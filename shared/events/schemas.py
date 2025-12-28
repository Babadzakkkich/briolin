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
    USER_PROFILE_UPDATE_REQUESTED = "user.profile_update_requested"  # Запрос на обновление профиля
    USER_PROFILE_UPDATED = "user.profile_updated"  # Подтверждение обновления профиля
    
    # События статуса
    USER_STATUS_CHANGE_REQUESTED = "user.status_change_requested"  # Запрос изменения статуса
    USER_STATUS_CHANGED = "user.status_changed"  # Подтверждение изменения статуса
    
    # События ролей
    USER_ROLES_UPDATE_REQUESTED = "user.roles_update_requested"  # Запрос обновления ролей
    USER_ROLES_UPDATED = "user.roles_updated"  # Подтверждение обновления ролей
    
    # События удаления
    USER_DELETION_REQUESTED = "user.deletion_requested"  # Запрос удаления
    USER_DELETED = "user.deleted"  # Подтверждение удаления

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