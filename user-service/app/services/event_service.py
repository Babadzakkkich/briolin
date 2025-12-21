# user-service/app/services/event_service.py
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
    
    async def publish_user_profile_created(
        self,
        keycloak_id: str,
        user_id: int,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        roles: List[str],
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события создания профиля пользователя в user-service"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_CREATED,
                source_service="user-service",
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
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_PROFILE_CREATED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_PROFILE_CREATED event for user: {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_PROFILE_CREATED event: {e}")
            return False
    
    async def publish_user_profile_updated(
        self,
        keycloak_id: str,
        user_id: int,
        updated_fields: Dict[str, Any],
        old_values: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события обновления профиля пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_PROFILE_UPDATED,
                source_service="user-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "updated_fields": updated_fields,
                    "old_values": old_values or {}
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_PROFILE_UPDATED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_PROFILE_UPDATED event for user: {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_PROFILE_UPDATED event: {e}")
            return False
    
    async def publish_user_status_changed(
        self,
        keycloak_id: str,
        user_id: int,
        is_active: bool,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события изменения статуса пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_STATUS_CHANGED,
                source_service="user-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "is_active": is_active,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_STATUS_CHANGED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_STATUS_CHANGED event for user: {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_STATUS_CHANGED event: {e}")
            return False
    
    async def publish_user_roles_updated(
        self,
        keycloak_id: str,
        user_id: int,
        roles: List[str],
        old_roles: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события обновления ролей пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_ROLES_UPDATED,
                source_service="user-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
                    "roles": roles,
                    "old_roles": old_roles or []
                }
            )
            
            success = await self.publisher.publish(
                exchange_name="briolin.events",
                routing_key=EventType.USER_ROLES_UPDATED,
                message=event.model_dump()
            )
            
            if success:
                logger.info(f"Published USER_ROLES_UPDATED event for user: {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_ROLES_UPDATED event: {e}")
            return False
    
    async def publish_user_deleted(
        self,
        keycloak_id: str,
        user_id: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Публикация события удаления пользователя"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_DELETED,
                source_service="user-service",
                correlation_id=correlation_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "user_id": user_id,
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
    global _event_service
    if _event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _event_service = EventService(rabbitmq_publisher)
    return _event_service