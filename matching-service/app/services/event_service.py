import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


class MatchingEventPublisher:
    def __init__(self):
        self.publisher = RabbitMQPublisher(settings.rabbitmq)

    async def connect(self):
        await self.publisher.connect()

    async def disconnect(self):
        await self.publisher.disconnect()

    async def publish_match_created(
        self, 
        user1_id: str, 
        user2_id: str, 
        chat_id: Optional[str] = None,
        match_id: Optional[int] = None
    ) -> bool:
        """Publish match.created event"""
        try:
            user_data = {
                "user1_id": user1_id,
                "user2_id": user2_id,
                "chat_id": chat_id
            }
            
            # ДОБАВИТЬ match_id если передан
            if match_id is not None:
                user_data["regular_match_id"] = match_id
            
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MATCH_CREATED,
                source_service=settings.service_name,
                correlation_id=str(uuid.uuid4()),
                user_data=user_data,
                metadata={
                    "service": settings.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event.mark_as_processed(settings.service_name)
            success = await self.publisher.publish_event(event)
            if success:
                logger.info(f"Published match.created event for {user1_id} and {user2_id}" + 
                        (f" (match_id={match_id})" if match_id else ""))
            else:
                logger.error("Failed to publish match.created event")
            return success
        except Exception as e:
            logger.error(f"Error publishing match.created: {e}")
            return False


event_publisher = MatchingEventPublisher()