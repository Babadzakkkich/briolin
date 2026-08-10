from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AvatarUploadResponse(BaseModel):
    """Ответ после загрузки аватарки"""
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')
    url: str = Field(..., description='URL ресурса')
    thumbnail_url: str = Field(..., description='URL уменьшенной версии изображения аватара')
    width: int = Field(..., description='Ширина изображения в пикселях')
    height: int = Field(..., description='Высота изображения в пикселях')
    file_size: int = Field(..., description='Размер файла в байтах')


class AvatarResponse(BaseModel):
    """Информация об аватарке (расширенная)"""
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')
    url: str = Field(..., description='URL ресурса')
    thumbnail_url: str = Field(..., description='URL уменьшенной версии изображения аватара')
    width: int = Field(..., description='Ширина изображения в пикселях')
    height: int = Field(..., description='Высота изображения в пикселях')
    file_size: int = Field(..., description='Размер файла в байтах')
    is_current: bool = Field(..., description='Признак того, что аватар является текущим')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    file_name: str = Field(..., description='Имя файла')


class AvatarDeleteResponse(BaseModel):
    """Ответ после удаления аватарки"""
    deleted: bool = Field(..., description='Признак успешного удаления')
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str = Field(..., description='Подробное описание ошибки')


# События для RabbitMQ
class AvatarUploadedEvent(BaseModel):
    """Событие: аватарка загружена"""
    event_type: str = Field('avatar.uploaded', description='Тип события загрузки аватара')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')
    url: str = Field(..., description='URL ресурса')
    thumbnail_url: str = Field(..., description='URL уменьшенной версии изображения аватара')
    width: int = Field(..., description='Ширина изображения в пикселях')
    height: int = Field(..., description='Высота изображения в пикселях')
    file_size: int = Field(..., description='Размер файла в байтах')
    is_current: bool = Field(True, description='Признак того, что аватар является текущим')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Дата и время события')


class AvatarDeletedEvent(BaseModel):
    """Событие: аватарка удалена"""
    event_type: str = Field('avatar.deleted', description='Тип события удаления аватара')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')
    is_current: bool = Field(False, description='Признак того, что аватар является текущим')
    soft_delete: bool = Field(True, description='Признак мягкого удаления без физического удаления данных')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Дата и время события')


class AvatarUpdatedEvent(BaseModel):
    """Событие: аватарка обновлена (смена текущей)"""
    event_type: str = Field('avatar.updated', description='Тип события обновления аватара')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    avatar_id: str = Field(..., description='Уникальный идентификатор аватара')
    is_current: bool = Field(True, description='Признак того, что аватар является текущим')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Дата и время события')