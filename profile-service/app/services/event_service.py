import uuid
import json
from datetime import datetime, date
from typing import Dict, Any, Optional

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


def json_serializer(obj):
    """Кастомный сериализатор для JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class EventService:
    """Сервис для работы с событиями в profile-service"""

    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher

    async def _publish_event(self, event: BaseEvent) -> bool:
        """Универсальный метод публикации события"""
        event.mark_as_processed(settings.service_name)

        # Конвертируем event в dict с правильной сериализацией
        event_dict = event.model_dump()
        
        # Дополнительная обработка для user_data, если там есть datetime/date
        if "user_data" in event_dict:
            for key, value in event_dict["user_data"].items():
                if isinstance(value, (datetime, date)):
                    event_dict["user_data"][key] = value.isoformat()
        
        # Создаем новый BaseEvent из обработанного dict
        processed_event = BaseEvent(**event_dict)

        success = await self.publisher.publish_event(processed_event)

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

    async def publish_profile_updated(
        self,
        keycloak_id: str,
        updated_fields: Dict[str, Any],
        correlation_id: str = None
    ) -> bool:
        """
        Публикация события обновления профиля для других сервисов (например, chat-service).
        Содержит информацию о том, какие поля были изменены.
        """
        try:
            correlation_id = correlation_id or str(uuid.uuid4())

            # Конвертируем datetime/date объекты в строки
            serialized_fields = {}
            for field, value in updated_fields.items():
                if isinstance(value, (datetime, date)):
                    serialized_fields[field] = value.isoformat()
                else:
                    serialized_fields[field] = value

            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_UPDATED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "updated_fields": serialized_fields,
                    "source_service": settings.service_name
                },
                metadata={
                    "profile_service_processed": True
                }
            )

            logger.info(f"Publishing PROFILE_UPDATED event for {keycloak_id}. Fields: {list(serialized_fields.keys())}")
            return await self._publish_event(event)

        except Exception as e:
            logger.error(f"Error publishing PROFILE_UPDATED event: {e}")
            return False


# Глобальный экземпляр
_event_service = None

def get_event_service() -> EventService:
    global _event_service
    if _event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _event_service = EventService(rabbitmq_publisher)
    return _event_service