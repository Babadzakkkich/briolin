from app.services.rabbitmq import rabbitmq_consumer
from . import user_consumers
from app.core.logger import logger

async def register_consumers():
    """Регистрация всех consumers"""
    try:
        # Подписка на события от user-service
        await user_consumers.register(rabbitmq_consumer)
        logger.info("All consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register consumers: {e}")
        raise