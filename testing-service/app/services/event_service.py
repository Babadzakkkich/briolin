import uuid
from typing import Dict, Any
from datetime import datetime

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from app.core.config import settings
from app.core.logger import logger


class TestingEventService:
    """Сервис для работы с событиями в testing-service"""
    
    def __init__(self, publisher: RabbitMQPublisher):
        self.publisher = publisher
    
    async def publish_test_started(
        self,
        keycloak_id: str,
        session_id: str,
        test_template_id: str
    ) -> bool:
        """Публикация события начала теста"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.TEST_STARTED,
                source_service=settings.service_name,
                correlation_id=session_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "session_id": session_id,
                    "test_template_id": test_template_id,
                    "started_at": datetime.utcnow().isoformat()
                },
                metadata={
                    "service": "testing-service"
                }
            )
            
            success = await self.publisher.publish_event(event)
            
            if success:
                logger.info(f"Published TEST_STARTED event for session {session_id}")
            else:
                logger.error(f"Failed to publish TEST_STARTED event")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing TEST_STARTED event: {e}")
            return False
    
    async def publish_test_completed(
        self,
        keycloak_id: str,
        session_id: str,
        results: Dict[str, Any]
    ) -> bool:
        """Публикация события завершения теста"""
        try:
            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.TEST_COMPLETED,
                source_service=settings.service_name,
                correlation_id=session_id,
                user_data={
                    "keycloak_id": keycloak_id,
                    "session_id": session_id,
                    "results": results,
                    "completed_at": datetime.utcnow().isoformat()
                },
                metadata={
                    "service": "testing-service",
                    "has_personality_results": True
                }
            )
            
            success = await self.publisher.publish_event(event)
            
            if success:
                logger.info(f"Published TEST_COMPLETED event for session {session_id}")
            else:
                logger.error(f"Failed to publish TEST_COMPLETED event")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing TEST_COMPLETED event: {e}")
            return False


# Глобальный экземпляр
_testing_event_service = None

def get_testing_event_service() -> TestingEventService:
    global _testing_event_service
    if _testing_event_service is None:
        from app.services.rabbitmq import rabbitmq_publisher
        _testing_event_service = TestingEventService(rabbitmq_publisher)
    return _testing_event_service