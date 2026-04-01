from app.services.rabbitmq import rabbitmq_consumer
from . import auth_consumers
from . import status_consumers
from . import media_consumers
from app.core.logger import logger


async def register_consumers():
    """Регистрация всех consumers"""
    try:
        await auth_consumers.register(rabbitmq_consumer)
        await status_consumers.register(rabbitmq_consumer)
        await media_consumers.register(rabbitmq_consumer)
        
        logger.info("All consumers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register consumers: {e}")
        raise