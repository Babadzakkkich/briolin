from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import signal
import logging

from app.core.config import settings
from app.core.logger import logger
from app.database.postgres.session import dispose_engine, engine
from app.database.postgres.models import Base
from app.core.exceptions import ChatServiceException
from app.core.exception_handlers import chat_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer
from app.services.websocket_manager import websocket_manager
from app.consumers import register_consumers
from app.websocket.routes import router as ws_router

async def shutdown_handler():
    """Обработчик graceful shutdown"""
    logger.info("Shutting down chat service gracefully...")
    
    await websocket_manager.stop_heartbeat_checker()
    await websocket_manager.disconnect_all()
    await rabbitmq_consumer.disconnect()
    await rabbitmq_publisher.disconnect()
    await dispose_engine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Chat Service...")
    
    # Инициализация PostgreSQL
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Подключение к RabbitMQ
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()
        await register_consumers()
        logger.info("Chat Service connected to RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
    
    # Регистрация обработчика сигналов
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown_handler()))
    
    yield
    
    logger.info("Shutting down Chat Service...")

app = FastAPI(
    title="Briolin Chat Service",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(ChatServiceException, chat_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API
app.include_router(api_router, prefix="/api/v1")

# WebSocket API
app.include_router(ws_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "chat-service",
        "websocket_connections": websocket_manager.get_connection_count()
    }

@app.get("/")
async def root():
    return {
        "service": "chat-service",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else None
    }