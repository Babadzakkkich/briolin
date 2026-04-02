# api-gateway/app/schemas/media.py
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
    """Информация об аватарке"""
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