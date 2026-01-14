from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import ProfileServiceException
from app.core.exception_handlers import profile_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer
from app.consumers import register_consumers

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Profile Service...")
    
    # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Подключение к RabbitMQ
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()
        
        # Регистрация consumers
        await register_consumers()
        
        logger.info("Profile Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
    
    yield
    
    logger.info("Shutting down Profile Service...")
    
    # Отключение от RabbitMQ
    try:
        await rabbitmq_consumer.disconnect()
        await rabbitmq_publisher.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    # Закрытие соединений с БД
    await dispose_engine()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(ProfileServiceException, profile_exception_handler)
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