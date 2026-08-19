from app.services.rabbitmq import rabbitmq_consumer
from . import profile_consumers
from app.core.logger import logger


async def register_consumers():
    """Регистрация всех consumers"""
    try:
        await profile_consumers.register(rabbitmq_consumer)
        logger.info("Matching service consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register consumers: {e}")
        raise