import uuid
import httpx
from typing import Optional, Tuple
from datetime import datetime

from app.services.minio_client import get_minio_client, MinIOClient
from app.services.image_processor import image_processor
from app.services.event_service import get_event_service
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedMediaTypeException,
    ImageProcessingException,
    FileNotFoundException
)
from app.schemas.media import AvatarUploadResponse, AvatarDeleteResponse


class MediaService:
    """Сервис для работы с медиафайлами"""
    
    def __init__(self):
        self.minio_client = get_minio_client()
        self.event_service = get_event_service()
    
    async def upload_avatar(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        keycloak_id: str
    ) -> AvatarUploadResponse:
        """
        Загрузка аватарки пользователя
        
        Args:
            file_data: Бинарные данные файла
            filename: Имя файла
            content_type: MIME тип файла
            keycloak_id: ID пользователя в Keycloak
        
        Returns:
            AvatarUploadResponse: Информация о загруженной аватарке
        """
        # Обработка изображения
        processed_data, processed_content_type, (width, height) = await image_processor.process_avatar(
            file_data, filename
        )
        
        # Генерируем уникальный ID
        avatar_id = str(uuid.uuid4())
        
        # Пути для хранения
        original_path = f"avatars/{keycloak_id}/{avatar_id}/original.webp"
        thumbnail_path = f"avatars/{keycloak_id}/{avatar_id}/thumbnail.webp"
        
        try:
            # Загружаем обработанное изображение
            await self.minio_client.upload_file(
                file_data=processed_data,
                object_name=original_path,
                content_type=processed_content_type
            )
            
            # Создаем и загружаем thumbnail
            thumbnail_data, thumbnail_content_type, (thumb_width, thumb_height) = await image_processor.create_thumbnail(
                processed_data
            )
            
            await self.minio_client.upload_file(
                file_data=thumbnail_data,
                object_name=thumbnail_path,
                content_type=thumbnail_content_type
            )
            
            # Получаем URL для доступа
            public_url = f"/media/avatar/{keycloak_id}?avatar_id={avatar_id}"
            thumbnail_url = f"/media/avatar/{keycloak_id}/thumbnail?avatar_id={avatar_id}"
            
            # Публикуем событие о загрузке аватарки
            await self.event_service.publish_avatar_uploaded(
                keycloak_id=keycloak_id,
                avatar_id=avatar_id,
                url=public_url,
                thumbnail_url=thumbnail_url,
                width=width,
                height=height,
                file_size=len(processed_data),
                is_current=True
            )
            
            logger.info(f"Avatar uploaded for user {keycloak_id}: {avatar_id}")
            
            return AvatarUploadResponse(
                avatar_id=avatar_id,
                url=public_url,
                thumbnail_url=thumbnail_url,
                width=width,
                height=height,
                file_size=len(processed_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to upload avatar: {e}")
            raise
    
    async def get_avatar(
        self,
        keycloak_id: str,
        avatar_id: str
    ) -> Tuple[bytes, str]:
        """
        Получение аватарки пользователя
        
        Args:
            keycloak_id: ID пользователя в Keycloak
            avatar_id: ID аватарки
        
        Returns:
            Tuple[bytes, str]: (данные файла, content_type)
        """
        try:
            object_name = f"avatars/{keycloak_id}/{avatar_id}/original.webp"
            file_data, content_type = await self.minio_client.get_file(object_name)
            return file_data, content_type
            
        except FileNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get avatar: {e}")
            raise
    
    async def get_avatar_thumbnail(
        self,
        keycloak_id: str,
        avatar_id: str
    ) -> Tuple[bytes, str]:
        """
        Получение thumbnail аватарки
        
        Args:
            keycloak_id: ID пользователя в Keycloak
            avatar_id: ID аватарки
        
        Returns:
            Tuple[bytes, str]: (данные файла, content_type)
        """
        try:
            object_name = f"avatars/{keycloak_id}/{avatar_id}/thumbnail.webp"
            file_data, content_type = await self.minio_client.get_file(object_name)
            return file_data, content_type
            
        except FileNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get thumbnail: {e}")
            raise
    
    async def delete_avatar(
        self,
        keycloak_id: str,
        avatar_id: str
    ) -> AvatarDeleteResponse:
        """
        Удаление аватарки пользователя
        
        Args:
            keycloak_id: ID пользователя в Keycloak
            avatar_id: ID аватарки
        
        Returns:
            AvatarDeleteResponse: Результат удаления
        """
        try:
            # Проверяем существование
            object_name = f"avatars/{keycloak_id}/{avatar_id}/original.webp"
            
            # Удаляем оригинал
            deleted_original = await self.minio_client.delete_file(object_name)
            
            if not deleted_original:
                raise FileNotFoundException(avatar_id)
            
            # Удаляем thumbnail
            thumbnail_name = f"avatars/{keycloak_id}/{avatar_id}/thumbnail.webp"
            await self.minio_client.delete_file(thumbnail_name)
            
            # Проверяем, является ли удаляемая аватарка текущей
            is_current = await self._is_current_avatar(keycloak_id, avatar_id)
            
            # Если удаляем текущую аватарку, отправляем событие
            if is_current:
                await self.event_service.publish_avatar_deleted(
                    keycloak_id=keycloak_id,
                    avatar_id=avatar_id,
                    is_current=True
                )
                logger.info(f"Deleted current avatar for user {keycloak_id}: {avatar_id}")
            else:
                logger.info(f"Deleted old avatar for user {keycloak_id}: {avatar_id} (not current)")
            
            return AvatarDeleteResponse(
                deleted=True,
                avatar_id=avatar_id
            )
            
        except FileNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete avatar: {e}", exc_info=True)
            raise
    
    async def _is_current_avatar(self, keycloak_id: str, avatar_id: str) -> bool:
        """
        Проверяет, является ли аватарка текущей для пользователя
        
        Args:
            keycloak_id: ID пользователя в Keycloak
            avatar_id: ID аватарки
        
        Returns:
            bool: True если аватарка текущая
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://profile-service:8003/api/v1/internal/profiles/{keycloak_id}/basic"
                )
                
                if response.status_code == 200:
                    profile_data = response.json()
                    current_avatar_id = None
                    
                    # Извлекаем avatar_id из URL
                    avatar_url = profile_data.get("avatar_url")
                    if avatar_url and "avatar_id=" in avatar_url:
                        current_avatar_id = avatar_url.split("avatar_id=")[1]
                    
                    return current_avatar_id == avatar_id
                    
                elif response.status_code == 404:
                    logger.warning(f"Profile not found for user {keycloak_id}")
                    return False
                else:
                    logger.warning(f"Failed to get profile for {keycloak_id}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking current avatar: {e}")
            return False


# Глобальный экземпляр
_media_service = None


def get_media_service() -> MediaService:
    """Получение экземпляра MediaService (синглтон)"""
    global _media_service
    if _media_service is None:
        _media_service = MediaService()
    return _media_service