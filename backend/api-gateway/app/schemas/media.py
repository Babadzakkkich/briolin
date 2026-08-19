# backend/api-gateway/app/schemas/media.py
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
    """Информация об аватарке"""
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