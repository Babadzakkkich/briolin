import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


class EventService:
    """Сервис для работы с событиями в user-service"""
    
    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher
    
    async def _publish_event(self, event: BaseEvent) -> bool:
        """Универсальный метод публикации события"""
        # Добавляем текущий сервис в processed_by
        event.mark_as_processed(settings.service_name)
        
        success = await self.publisher.publish_event(event)
        
        if success:
            logger.info(f"Published {event.event_type.value} event (ID: {event.event_id[:8]})")
        else:
            logger.error(f"Failed to publish {event.event_type.value} event")
        
        return success
    
    async def publish_user_profile_created(
        self,
        keycloak_id: str,
        user_id: int,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        roles: List[str],
        correlation_id: str = None
    ) -> bool:
        """Публикация события создания профиля пользователя в user-service"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_CREATED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "roles": roles,
                    "is_active": True
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing USER_PROFILE_CREATED event: {e}")
            return False
    
    async def publish_user_profile_update_requested(
        self,
        keycloak_id: str,
        user_id: int,
        updated_fields: Dict[str, Any],
        old_values: Optional[Dict[str, Any]] = None,
        correlation_id: str = None
    ) -> bool:
        """Публикация события запроса обновления профиля пользователя"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_UPDATE_REQUESTED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "updated_fields": updated_fields,
                    "old_values": old_values or {}
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing USER_PROFILE_UPDATE_REQUESTED event: {e}")
            return False
    
    async def publish_user_status_change_requested(
        self,
        keycloak_id: str,
        user_id: int,
        is_active: bool,
        reason: Optional[str] = None,
        correlation_id: str = None
    ) -> bool:
        """Публикация события запроса изменения статуса пользователя"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_STATUS_CHANGE_REQUESTED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "is_active": is_active,
                    "reason": reason
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing USER_STATUS_CHANGE_REQUESTED event: {e}")
            return False
    
    async def publish_user_roles_update_requested(
        self,
        keycloak_id: str,
        user_id: int,
        roles: List[str],
        old_roles: Optional[List[str]] = None,
        correlation_id: str = None
    ) -> bool:
        """Публикация события запроса обновления ролей пользователя"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_ROLES_UPDATE_REQUESTED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "roles": roles,
                    "old_roles": old_roles or []
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing USER_ROLES_UPDATE_REQUESTED event: {e}")
            return False
    
    async def publish_user_deletion_requested(
        self,
        keycloak_id: str,
        user_id: Optional[int] = None,
        correlation_id: str = None
    ) -> bool:
        """Публикация события запроса удаления пользователя"""
        try:
            correlation_id = correlation_id or str(uuid.uuid4())
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_DELETION_REQUESTED,
                source_service=settings.service_name,
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id
                }
            )
            
            return await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Error publishing USER_DELETION_REQUESTED event: {e}")
            return False


# Глобальный экземпляр
_event_service = None

def get_event_service() -> EventService:
    global _event_service
    if _event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _event_service = EventService(rabbitmq_publisher)
    return _event_service