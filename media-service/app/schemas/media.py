from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
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
    """Информация об аватарке (расширенная)"""
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str = Field(..., description="ID аватарки")
    url: str = Field(..., description="URL для доступа к аватарке")
    thumbnail_url: str = Field(..., description="URL thumbnail")
    width: int = Field(..., description="Ширина изображения")
    height: int = Field(..., description="Высота изображения")
    file_size: int = Field(..., description="Размер файла в байтах")
    is_current: bool = Field(..., description="Является ли текущей аватаркой")
    created_at: datetime = Field(..., description="Дата загрузки")
    file_name: str = Field(..., description="Оригинальное имя файла")


class AvatarDeleteResponse(BaseModel):
    """Ответ после удаления аватарки"""
    deleted: bool = Field(..., description="Удалено ли")
    avatar_id: str = Field(..., description="ID удаленной аватарки")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str = Field(..., description="Описание ошибки")


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
    is_current: bool = Field(True, description="Является ли текущей")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AvatarDeletedEvent(BaseModel):
    """Событие: аватарка удалена"""
    event_type: str = "avatar.deleted"
    keycloak_id: str
    avatar_id: str
    is_current: bool = Field(False, description="Была ли текущей")
    soft_delete: bool = Field(True, description="Soft delete или hard delete")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AvatarUpdatedEvent(BaseModel):
    """Событие: аватарка обновлена (смена текущей)"""
    event_type: str = "avatar.updated"
    keycloak_id: str
    avatar_id: str
    is_current: bool = Field(True, description="Новый статус")
    timestamp: datetime = Field(default_factory=datetime.utcnow)