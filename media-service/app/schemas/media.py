from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class AvatarUploadResponse(BaseModel):
    """Ответ после загрузки аватарки"""
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str = Field(..., description="ID аватарки")
    url: str = Field(..., description="URL для доступа к аватарке")
    thumbnail_url: str = Field(..., description="URL thumbnail")
    width: int = Field(..., description="Ширина изображения")
    height: int = Field(..., description="Высота изображения")
    file_size: int = Field(..., description="Размер файла в байтах")


class AvatarResponse(BaseModel):
    """Информация об аватарке"""
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str
    url: str
    thumbnail_url: str
    width: int
    height: int
    file_size: int
    created_at: datetime


class AvatarDeleteResponse(BaseModel):
    """Ответ после удаления аватарки"""
    deleted: bool
    avatar_id: str


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str


# События для RabbitMQ
class AvatarUploadedEvent(BaseModel):
    """Событие: аватарка загружена"""
    event_type: str = "avatar.uploaded"
    keycloak_id: str
    avatar_id: str
    url: str
    thumbnail_url: str
    width: int
    height: int
    file_size: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AvatarDeletedEvent(BaseModel):
    """Событие: аватарка удалена"""
    event_type: str = "avatar.deleted"
    keycloak_id: str
    avatar_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)