from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import MediaServiceException
from app.core.exception_handlers import media_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Media Service...")
    
    # Подключение к RabbitMQ
    rabbitmq_connected = False
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()
        rabbitmq_connected = True
        logger.info("Media Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
    
    yield
    
    logger.info("Shutting down Media Service...")
    
    # Отключение от RabbitMQ
    if rabbitmq_connected:
        try:
            await rabbitmq_consumer.disconnect()
            await rabbitmq_publisher.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(MediaServiceException, media_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "rabbitmq": "connected" if rabbitmq_publisher._is_connected else "disconnected"
    }


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else None
    }