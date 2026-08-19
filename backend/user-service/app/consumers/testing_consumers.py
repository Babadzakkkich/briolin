from datetime import datetime
from typing import Dict, Any

from shared.events.schemas import EventType
from app.services.rabbitmq import rabbitmq_consumer
from app.services.user_service import UserService
from app.database.session import async_session_factory
from app.core.config import settings
from app.core.logger import logger

async def handle_test_completed(event: Dict[str, Any]) -> bool:
    """Обработка события завершения теста из testing-service"""
    try:
        from shared.events.schemas import BaseEvent
        
        base_event = BaseEvent(**event)
        
        if base_event.is_processed_by(settings.service_name):
            logger.debug(f"Event {base_event.event_id[:8]} already processed by user-service")
            return True
        
        user_data = event.get("user_data", {})
        keycloak_id = user_data.get("keycloak_id")
        results = user_data.get("results", {})
        
        if not keycloak_id:
            logger.error("Missing keycloak_id in test completed event")
            return False
        
        passed = results.get("passed", False)
        
        logger.info(f"Processing test completion for {keycloak_id} - Passed: {passed}")
        
        if passed:
            async with async_session_factory() as session:
                from app.services.keycloak_client import KeycloakClient
                kc_client = KeycloakClient()
                user_service = UserService(session, kc_client)
                
                user = await user_service.get_user_by_keycloak_id(keycloak_id)
                
                if not user:
                    logger.warning(f"User {keycloak_id} not found in user-service")
                    return False
                
                user.is_test_passed = True
                await session.commit()
                
                logger.info(f"User {keycloak_id} marked as test passed")
        
        return True
            
    except Exception as e:
        logger.error(f"Error handling test completed: {e}", exc_info=True)
        return False

async def register(consumer):
    """Регистрация consumers для событий от testing-service"""
    try:
        await consumer.consume_user_events(
            event_type=EventType.TEST_COMPLETED,
            callback=handle_test_completed
        )
        
        logger.info("Testing event consumers registered successfully in user-service")
    except Exception as e:
        logger.error(f"Failed to register testing consumers: {e}", exc_info=True)
        raise