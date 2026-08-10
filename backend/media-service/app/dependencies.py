# app/dependencies.py
import asyncio
from typing import Tuple, Optional, AsyncGenerator
from fastapi import Depends, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedMediaTypeException
)
from app.core.logger import logger
from app.database.session import async_session_factory
from app.services.media_service import MediaService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии базы данных"""
    async with async_session_factory() as session:
        yield session


async def validate_file(file: UploadFile) -> Tuple[bytes, str]:
    """
    Валидирует загруженный файл:
    - Размер
    - MIME тип
    """
    # Проверяем размер
    content = await file.read()
    
    if len(content) > settings.service.max_file_size:
        raise FileTooLargeException(settings.service.max_file_size)
    
    # Проверяем MIME тип
    content_type = file.content_type or ""
    if content_type not in settings.service.allowed_mime_types:
        raise UnsupportedMediaTypeException(settings.service.allowed_mime_types)
    
    return content, content_type


def get_media_service(db: AsyncSession = Depends(get_db)) -> MediaService:
    """Получение экземпляра MediaService с сессией БД"""
    return MediaService(db)


def require_admin():
    """Декоратор для проверки прав администратора"""
    async def admin_checker(current_user: dict = Depends(get_current_user)):
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return current_user
    return admin_checker


__all__ = [
    'get_db',
    'get_current_user',
    'validate_file',
    'get_media_service',
    'require_admin'
]