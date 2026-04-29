import uuid
from datetime import datetime
from typing import Optional

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


class EventService:
    """Сервис для работы с событиями"""
    
    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher
    
    async def publish_avatar_uploaded(
        self,
        keycloak_id: str,
        avatar_id: str,
        url: str,
        thumbnail_url: str,
        width: int,
        height: int,
        file_size: int,
        is_current: bool = True,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикует событие о загрузке аватарки"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.AVATAR_UPLOADED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "avatar_id": avatar_id,
                    "url": url,
                    "thumbnail_url": thumbnail_url,
                    "width": width,
                    "height": height,
                    "file_size": file_size,
                    "is_current": is_current
                }
            )
            
            success = await self.publisher.publish_event(event)
            
            if success:
                logger.info(f"Published AVATAR_UPLOADED event for {keycloak_id}")
            else:
                logger.error(f"Failed to publish AVATAR_UPLOADED event")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing avatar uploaded event: {e}")
            return False
    
    async def publish_avatar_deleted(
        self,
        keycloak_id: str,
        avatar_id: str,
        is_current: bool = False,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикует событие об удалении аватарки"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.AVATAR_DELETED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "avatar_id": avatar_id,
                    "is_current": is_current
                }
            )
            
            success = await self.publisher.publish_event(event)
            
            if success:
                logger.info(f"Published AVATAR_DELETED event for {keycloak_id}")
            else:
                logger.error(f"Failed to publish AVATAR_DELETED event")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing avatar deleted event: {e}")
            return False
    
    async def publish_avatar_updated(
        self,
        keycloak_id: str,
        avatar_id: str,
        is_current: bool = True,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикует событие об обновлении аватарки (смена текущей)"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.AVATAR_UPDATED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "avatar_id": avatar_id,
                    "is_current": is_current
                }
            )
            
            success = await self.publisher.publish_event(event)
            
            if success:
                logger.info(f"Published AVATAR_UPDATED event for {keycloak_id}")
            else:
                logger.error(f"Failed to publish AVATAR_UPDATED event")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing avatar updated event: {e}")
            return False


# Глобальный экземпляр
_event_service = None


def get_event_service() -> EventService:
    """Получение экземпляра EventService (синглтон)"""
    global _event_service
    if _event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _event_service = EventService(rabbitmq_publisher)
    return _event_service