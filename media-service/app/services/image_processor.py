import io
from PIL import Image
from typing import Tuple, Optional
import asyncio
from functools import partial

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import ImageProcessingException


class ImageProcessor:
    """Обработка изображений (ресайз, конвертация, создание thumbnails)"""
    
    @staticmethod
    async def process_avatar(
        file_data: bytes,
        original_filename: str
    ) -> Tuple[bytes, str, Tuple[int, int]]:
        """
        Обрабатывает аватарку:
        - Проверяет размеры
        - Ресайзит если нужно
        - Конвертирует в WebP
        - Создает thumbnail
        
        Returns:
            Tuple[bytes, str, Tuple[int, int]]: (processed_data, content_type, (width, height))
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Открываем изображение
            image = await loop.run_in_executor(
                None,
                partial(Image.open, io.BytesIO(file_data))
            )
            
            # Конвертируем в RGB если нужно (для JPEG/PNG)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Получаем исходные размеры
            original_width, original_height = image.size
            
            # Ресайз если превышает лимиты
            max_size = settings.service.max_width
            if original_width > max_size or original_height > max_size:
                ratio = min(max_size / original_width, max_size / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                image = await loop.run_in_executor(
                    None,
                    partial(image.resize, (new_width, new_height), Image.Resampling.LANCZOS)
                )
                logger.debug(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
            
            # Сохраняем в WebP
            output = io.BytesIO()
            await loop.run_in_executor(
                None,
                partial(image.save, output, format='WEBP', quality=85, optimize=True)
            )
            
            processed_data = output.getvalue()
            content_type = 'image/webp'
            width, height = image.size
            
            logger.debug(f"Processed avatar: {width}x{height}, size: {len(processed_data)} bytes")
            
            return processed_data, content_type, (width, height)
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ImageProcessingException(f"Failed to process image: {str(e)}")
    
    @staticmethod
    async def create_thumbnail(
        file_data: bytes
    ) -> Tuple[bytes, str, Tuple[int, int]]:
        """Создает thumbnail изображения"""
        try:
            loop = asyncio.get_event_loop()
            
            image = await loop.run_in_executor(
                None,
                partial(Image.open, io.BytesIO(file_data))
            )
            
            # Конвертируем в RGB
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Создаем квадратный thumbnail
            size = settings.service.thumbnail_size
            width, height = image.size
            
            # Обрезаем до квадрата
            min_side = min(width, height)
            left = (width - min_side) // 2
            top = (height - min_side) // 2
            image = await loop.run_in_executor(
                None,
                partial(image.crop, (left, top, left + min_side, top + min_side))
            )
            
            # Ресайз
            image = await loop.run_in_executor(
                None,
                partial(image.resize, (size, size), Image.Resampling.LANCZOS)
            )
            
            # Сохраняем
            output = io.BytesIO()
            await loop.run_in_executor(
                None,
                partial(image.save, output, format='WEBP', quality=75, optimize=True)
            )
            
            thumbnail_data = output.getvalue()
            
            logger.debug(f"Created thumbnail: {size}x{size}, size: {len(thumbnail_data)} bytes")
            
            return thumbnail_data, 'image/webp', (size, size)
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            raise ImageProcessingException(f"Failed to create thumbnail: {str(e)}")


# Глобальный экземпляр
image_processor = ImageProcessor()