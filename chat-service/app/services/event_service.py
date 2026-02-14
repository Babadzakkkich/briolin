import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from shared.events.schemas import BaseEvent, EventType, UserOnlineEvent, UserOfflineEvent, UserHeartbeatEvent
from app.services.rabbitmq import rabbitmq_publisher
from app.core.config import settings
from app.core.logger import logger

class EventService:
    """Сервис для публикации событий онлайн-статуса"""
    
    async def publish_user_online(self, keycloak_id: str, connection_id: Optional[str] = None) -> bool:
        """Публикация события USER_ONLINE"""
        try:
            event = UserOnlineEvent(
                event_id=str(uuid.uuid4()),
                keycloak_id=keycloak_id,
                connection_id=connection_id,
                metadata={
                    "service": settings.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            base_event = event.to_base_event()
            base_event.mark_as_processed(settings.service_name)
            
            success = await rabbitmq_publisher.publish_event(base_event)
            
            if success:
                logger.info(f"Published USER_ONLINE event for {keycloak_id}")
            else:
                logger.error(f"Failed to publish USER_ONLINE event for {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_ONLINE event: {e}")
            return False
    
    async def publish_user_offline(
        self, 
        keycloak_id: str, 
        connection_id: Optional[str] = None,
        reason: str = "disconnect"
    ) -> bool:
        """Публикация события USER_OFFLINE"""
        try:
            event = UserOfflineEvent(
                event_id=str(uuid.uuid4()),
                keycloak_id=keycloak_id,
                connection_id=connection_id,
                reason=reason,
                metadata={
                    "service": settings.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            base_event = event.to_base_event()
            base_event.mark_as_processed(settings.service_name)
            
            success = await rabbitmq_publisher.publish_event(base_event)
            
            if success:
                logger.info(f"Published USER_OFFLINE event for {keycloak_id} (reason: {reason})")
            else:
                logger.error(f"Failed to publish USER_OFFLINE event for {keycloak_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing USER_OFFLINE event: {e}")
            return False
    
    async def publish_user_heartbeat(self, keycloak_id: str, connection_id: str) -> bool:
        """Публикация события USER_HEARTBEAT (опционально, для статистики)"""
        try:
            event = UserHeartbeatEvent(
                event_id=str(uuid.uuid4()),
                keycloak_id=keycloak_id,
                connection_id=connection_id,
                metadata={
                    "service": settings.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            base_event = event.to_base_event()
            base_event.mark_as_processed(settings.service_name)
            
            # Heartbeat события не критичны, поэтому не логируем ошибки
            return await rabbitmq_publisher.publish_event(base_event)
            
        except Exception as e:
            logger.debug(f"Error publishing USER_HEARTBEAT event: {e}")
            return False

# Глобальный экземпляр
_event_service = None

def get_event_service() -> EventService:
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service