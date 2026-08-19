from contextlib import asynccontextmanager
from datetime import datetime

from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.exception_handlers import (
    global_exception_handler,
    testing_exception_handler,
)
from app.core.exceptions import TestingException
from app.core.logger import logger
from app.database.models import Base
from app.database.session import dispose_engine, engine
from app.services.rabbitmq import rabbitmq_consumer, rabbitmq_publisher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Testing Service...")

    # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Подключение к RabbitMQ
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()


        logger.info("Testing Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")

    yield

    logger.info("Shutting down Testing Service...")

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
app.add_exception_handler(TestingException, testing_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "testing-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Briolin Testing Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else None
    }
