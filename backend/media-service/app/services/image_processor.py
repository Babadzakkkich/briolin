import io
from PIL import Image, ImageFilter
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
        - Приводит к фиксированному размеру (квадрат)
        - Добавляет размытый фон для неквадратных изображений
        - Конвертирует в WebP
        
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
            
            # Конвертируем в RGB/RGBA
            if image.mode in ('RGBA', 'LA', 'P'):
                if image.mode == 'P':
                    image = image.convert('RGBA')
                # Сохраняем альфа-канал для правильной обработки
                has_alpha = image.mode in ('RGBA', 'LA')
            else:
                image = image.convert('RGB')
                has_alpha = False
            
            target_size = settings.service.avatar_size  # 1024
            
            # Создаем квадратное изображение с размытым фоном
            # ИСПРАВЛЕНО: используем лямбду или ссылку на метод класса
            processed = await loop.run_in_executor(
                None,
                lambda: ImageProcessor._make_square_with_blurred_background(
                    image, target_size, has_alpha
                )
            )
            
            # Сохраняем в WebP
            output = io.BytesIO()
            await loop.run_in_executor(
                None,
                partial(
                    processed.save, 
                    output, 
                    format='WEBP', 
                    quality=85, 
                    optimize=True,
                )
            )
            
            processed_data = output.getvalue()
            
            logger.debug(
                f"Processed avatar: {target_size}x{target_size}, "
                f"size: {len(processed_data)} bytes"
            )
            
            return processed_data, 'image/webp', (target_size, target_size)
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ImageProcessingException(f"Failed to process image: {str(e)}")


    @staticmethod
    def _make_square_with_blurred_background(
        image: Image.Image, 
        target_size: int, 
        has_alpha: bool = False
    ) -> Image.Image:
        """
        Создает квадратное изображение с размытым фоном.
        - Если изображение больше target_size → уменьшает
        - Если изображение меньше target_size → увеличивает с размытым фоном
        - Для альфа-канала используется прозрачный фон.
        """
        width, height = image.size
        
        # Если уже квадрат и правильного размера
        if width == height == target_size:
            return image
        
        # Создаем фон
        if has_alpha:
            # Для RGBA - прозрачный фон
            background = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        else:
            # Для RGB - размытый фон из исходного изображения
            bg_image = image.copy()
            bg_image = bg_image.resize((target_size, target_size), Image.Resampling.LANCZOS)
            bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=20))
            background = bg_image
        
        # Ресайзим изображение, сохраняя пропорции
        # Используем min чтобы изображение полностью поместилось (с фоном по краям)
        # Используем max чтобы изображение заполнило всё (с обрезкой краёв)
        ratio = min(target_size / width, target_size / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Используем качественный ресайз
        if new_width < target_size or new_height < target_size:
            # Увеличиваем до нужного размера
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Уменьшаем до нужного размера
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Центрируем
        x_offset = (target_size - new_width) // 2
        y_offset = (target_size - new_height) // 2
        
        # Вставляем на фон
        if has_alpha:
            background.paste(resized, (x_offset, y_offset), resized)
        else:
            background.paste(resized, (x_offset, y_offset))
        
        return background
    
    @staticmethod
    async def create_thumbnail(
        file_data: bytes
    ) -> Tuple[bytes, str, Tuple[int, int]]:
        """
        Создает thumbnail изображения.
        Теперь просто ресайзит, так как оригинал уже квадратный.
        """
        try:
            loop = asyncio.get_event_loop()
            
            image = await loop.run_in_executor(
                None,
                partial(Image.open, io.BytesIO(file_data))
            )
            
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(
                    image, 
                    mask=image.split()[-1] if image.mode == 'RGBA' else None
                )
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            size = settings.service.thumbnail_size  # 200
            
            # Теперь просто ресайз, так как оригинал уже квадратный
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
            
            logger.debug(
                f"Created thumbnail: {size}x{size}, "
                f"size: {len(thumbnail_data)} bytes"
            )
            
            return thumbnail_data, 'image/webp', (size, size)
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            raise ImageProcessingException(f"Failed to create thumbnail: {str(e)}")


# Глобальный экземпляр
image_processor = ImageProcessor()