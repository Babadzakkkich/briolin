# app/services/media_service.py
import uuid
from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.minio_client import get_minio_client, MinIOClient
from app.services.image_processor import image_processor
from app.services.event_service import get_event_service
from app.database.models import Avatar
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedMediaTypeException,
    ImageProcessingException,
    FileNotFoundException,
    MaxAvatarsExceededException
)
from app.schemas.media import AvatarUploadResponse, AvatarDeleteResponse, AvatarResponse


class MediaService:
    """Сервис для работы с медиафайлами"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.minio_client = get_minio_client()
        self.event_service = get_event_service()
    
    async def _get_avatar_count(self, keycloak_id: str) -> int:
        """Получает количество аватарок пользователя"""
        stmt = select(Avatar).where(
            and_(
                Avatar.keycloak_id == keycloak_id,
                Avatar.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
    
    async def _reset_current_avatar(self, keycloak_id: str) -> None:
        """Сбрасывает флаг is_current у всех аватарок пользователя"""
        stmt = update(Avatar).where(
            and_(
                Avatar.keycloak_id == keycloak_id,
                Avatar.is_deleted == False
            )
        ).values(is_current=False)
        await self.db.execute(stmt)
    
    async def _select_next_avatar(self, keycloak_id: str) -> None:
        """Выбирает следующую аватарку как текущую после удаления текущей"""
        stmt = select(Avatar).where(
            and_(
                Avatar.keycloak_id == keycloak_id,
                Avatar.is_deleted == False
            )
        ).order_by(Avatar.created_at.desc()).limit(1)
        
        result = await self.db.execute(stmt)
        next_avatar = result.scalar_one_or_none()
        
        if next_avatar:
            next_avatar.is_current = True
            await self.db.flush()
            
            # Публикуем событие о смене аватарки
            await self.event_service.publish_avatar_updated(
                keycloak_id=keycloak_id,
                avatar_id=next_avatar.id,
                is_current=True
            )
    
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
        # Проверяем лимит аватарок
        avatar_count = await self._get_avatar_count(keycloak_id)
        if avatar_count >= settings.service.max_avatars_per_user:
            raise MaxAvatarsExceededException(settings.service.max_avatars_per_user)
        
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
            
            # Сбрасываем флаг is_current у всех аватарок
            await self._reset_current_avatar(keycloak_id)
            
            # Сохраняем в БД
            avatar = Avatar(
                id=avatar_id,
                keycloak_id=keycloak_id,
                file_name=filename,
                file_size=len(processed_data),
                width=width,
                height=height,
                original_path=original_path,
                thumbnail_path=thumbnail_path,
                is_current=True,
                is_deleted=False
            )
            self.db.add(avatar)
            await self.db.commit()
            await self.db.refresh(avatar)
            
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
            await self.db.rollback()
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
            # Проверяем существование в БД
            stmt = select(Avatar).where(
                and_(
                    Avatar.id == avatar_id,
                    Avatar.keycloak_id == keycloak_id,
                    Avatar.is_deleted == False
                )
            )
            result = await self.db.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                raise FileNotFoundException(avatar_id)
            
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
            # Проверяем существование в БД
            stmt = select(Avatar).where(
                and_(
                    Avatar.id == avatar_id,
                    Avatar.keycloak_id == keycloak_id,
                    Avatar.is_deleted == False
                )
            )
            result = await self.db.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                raise FileNotFoundException(avatar_id)
            
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
        Удаление аватарки пользователя (soft delete)
        
        Args:
            keycloak_id: ID пользователя в Keycloak
            avatar_id: ID аватарки
        
        Returns:
            AvatarDeleteResponse: Результат удаления
        """
        try:
            # Находим аватарку в БД
            stmt = select(Avatar).where(
                and_(
                    Avatar.id == avatar_id,
                    Avatar.keycloak_id == keycloak_id,
                    Avatar.is_deleted == False
                )
            )
            result = await self.db.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                raise FileNotFoundException(avatar_id)
            
            was_current = avatar.is_current
            
            # Soft delete
            avatar.is_deleted = True
            avatar.is_current = False
            
            # Если удаляем текущую аватарку, выбираем другую
            if was_current:
                await self._select_next_avatar(keycloak_id)
            
            await self.db.commit()
            
            # Публикуем событие об удалении
            await self.event_service.publish_avatar_deleted(
                keycloak_id=keycloak_id,
                avatar_id=avatar_id,
                is_current=was_current
            )
            
            logger.info(f"Avatar deleted for user {keycloak_id}: {avatar_id} (was_current={was_current})")
            
            return AvatarDeleteResponse(
                deleted=True,
                avatar_id=avatar_id
            )
            
        except FileNotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete avatar: {e}", exc_info=True)
            raise
    
    async def get_user_avatars(
        self,
        keycloak_id: str,
        include_deleted: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[AvatarResponse]:
        """Получение всех аватарок пользователя"""
        stmt = select(Avatar).where(Avatar.keycloak_id == keycloak_id)
        
        if not include_deleted:
            stmt = stmt.where(Avatar.is_deleted == False)
        
        stmt = stmt.order_by(Avatar.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        avatars = result.scalars().all()
        
        return [
            AvatarResponse(
                avatar_id=a.id,
                url=f"/media/avatar/{keycloak_id}?avatar_id={a.id}",
                thumbnail_url=f"/media/avatar/{keycloak_id}/thumbnail?avatar_id={a.id}",
                width=a.width,
                height=a.height,
                file_size=a.file_size,
                is_current=a.is_current,
                created_at=a.created_at,
                file_name=a.file_name
            )
            for a in avatars
        ]
    
    async def set_current_avatar(
        self,
        keycloak_id: str,
        avatar_id: str
    ) -> bool:
        """Установка активной аватарки"""
        try:
            # Сбрасываем текущий флаг
            await self._reset_current_avatar(keycloak_id)
            
            # Устанавливаем новый
            stmt = update(Avatar).where(
                and_(
                    Avatar.keycloak_id == keycloak_id,
                    Avatar.id == avatar_id,
                    Avatar.is_deleted == False
                )
            ).values(is_current=True)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return False
            
            # Публикуем событие об обновлении аватарки
            await self.event_service.publish_avatar_updated(
                keycloak_id=keycloak_id,
                avatar_id=avatar_id,
                is_current=True
            )
            
            logger.info(f"Current avatar changed for user {keycloak_id}: {avatar_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to set current avatar: {e}")
            return False
    
    async def hard_delete_avatar(
        self,
        keycloak_id: str,
        avatar_id: str
    ) -> bool:
        """
        Полное удаление аватарки (удаление файлов из MinIO и записи из БД)
        Только для администраторов или фоновых задач
        """
        try:
            # Находим аватарку
            stmt = select(Avatar).where(
                and_(
                    Avatar.id == avatar_id,
                    Avatar.keycloak_id == keycloak_id
                )
            )
            result = await self.db.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                return False
            
            # Удаляем файлы из MinIO
            await self.minio_client.delete_file(avatar.original_path)
            await self.minio_client.delete_file(avatar.thumbnail_path)
            
            # Удаляем запись из БД
            await self.db.delete(avatar)
            await self.db.commit()
            
            logger.info(f"Avatar hard deleted for user {keycloak_id}: {avatar_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to hard delete avatar: {e}")
            return False