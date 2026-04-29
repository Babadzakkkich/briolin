from app.services.rabbitmq import rabbitmq_consumer
from . import user_consumers
from . import profile_consumers
from . import match_consumers
from . import media_consumers
from app.core.logger import logger


async def register_consumers():
    """Регистрация всех consumers"""
    try:
        # Подписка на события от user-service
        await user_consumers.register(rabbitmq_consumer)

        # Подписка на события от profile-service
        await profile_consumers.register(rabbitmq_consumer)
        
        # Подписка на события от matching-service (матчи)
        await match_consumers.register(rabbitmq_consumer)
        
        # Подписка на события от media-service (аватарки)
        await media_consumers.register(rabbitmq_consumer)

        logger.info("Chat service consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register consumers: {e}")
        raise