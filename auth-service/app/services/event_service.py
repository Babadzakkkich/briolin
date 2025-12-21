# auth-service/app/services/event_service.py
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


class EventService:
    """Сервис для работы с событиями в auth-service"""
    
    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher
    
    async def publish_user_registered(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        role: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события регистрации пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_REGISTERED,
                source_service="auth-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "is_active": True
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_REGISTERED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_REGISTERED event for user: {username}")
            else:
                logger.error(f"Failed to publish USER_REGISTERED event for user: {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_REGISTERED event: {e}")
            return False
    
    async def publish_user_updated(
        self,
        keycloak_id: str,
        updated_fields: Dict[str, Any],
        old_values: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события обновления пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_UPDATED,
                source_service="auth-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "updated_fields": updated_fields,
                    "old_values": old_values or {}
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_UPDATED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_UPDATED event for user: {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_UPDATED event: {e}")
            return False
    
    async def publish_user_deleted(
        self, 
        keycloak_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события удаления пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_DELETED,
                source_service="auth-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_DELETED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_DELETED event for user: {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_DELETED event: {e}")
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