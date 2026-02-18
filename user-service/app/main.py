from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import UserServiceException
from app.core.exception_handlers import user_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer
from app.consumers import register_consumers
from app.services.event_waiter import get_event_waiter

async def cleanup_old_waiters_periodically():
    """Периодическая очистка старых ожиданий событий"""
    while True:
        try:
            event_waiter = get_event_waiter()
            await event_waiter.cleanup_old_waiters()
            await asyncio.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            logger.error(f"Error in cleanup_old_waiters_periodically: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting User Service...")
    
    # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Запускаем фоновую задачу очистки
    cleanup_task = asyncio.create_task(cleanup_old_waiters_periodically())
    
    # Подключение к RabbitMQ
    try:
        await rabbitmq_publisher.connect()
        logger.info("User Service publisher connected to RabbitMQ")
        
        await rabbitmq_consumer.connect()
        logger.info("User Service consumer connected to RabbitMQ")
        
        # Регистрация consumers
        await register_consumers()
        
        logger.info("User Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
        # Можно продолжить работу без RabbitMQ
    
    yield
    
    logger.info("Shutting down User Service...")
    
    # Отменяем фоновую задачу
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # Отключение от RabbitMQ
    try:
        await rabbitmq_consumer.disconnect()
        await rabbitmq_publisher.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    await dispose_engine()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(UserServiceException, user_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}