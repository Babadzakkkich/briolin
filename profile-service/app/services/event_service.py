import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger

class EventService:
    """Сервис для работы с событиями в profile-service"""
    
    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher
    
    async def _publish_event(self, event: BaseEvent) -> bool:
        """Универсальный метод публикации события"""
        event.mark_as_processed(settings.service_name)
        
        success = await self.publisher.publish_event(event)
        
        if success:
            logger.info(f"Published {event.event_type.value} event (ID: {event.event_id[:8]})")
        else:
            logger.error(f"Failed to publish {event.event_type.value} event")
        
        return success
    
    async def publish_keycloak_update_requested(
        self,
        keycloak_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        correlation_id: str = None
    ) -> bool:
        """Публикация события запроса обновления имени в Keycloak"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            update_data = {}
            if first_name:
                update_data["first_name"] = first_name
            if last_name:
                update_data["last_name"] = last_name
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_UPDATE_REQUESTED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "updated_fields": update_data,
                    "source_service": "profile-service"
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing Keycloak update event: {e}")
            return False

# Глобальный экземпляр
_event_service = None

def get_event_service() -> EventService:
    global _event_service
    if _event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _event_service = EventService(rabbitmq_publisher)
    return _event_service