from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import EmailException
from app.core.exception_handlers import email_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.consumer import start_consumer, stop_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Email Service...")
    
    # Запуск RabbitMQ consumer
    try:
        await start_consumer()
        logger.info("Email consumer started")
    except Exception as e:
        logger.error(f"Failed to start email consumer: {e}")
    
    logger.info("Email Service started successfully")
    
    yield
    
    logger.info("Shutting down Email Service...")
    
    # Остановка consumer
    try:
        await stop_consumer()
        logger.info("Email consumer stopped")
    except Exception as e:
        logger.error(f"Error stopping email consumer: {e}")
    
    logger.info("Email Service shutdown complete")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(EmailException, email_exception_handler)
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
    from app.services.consumer import is_consumer_running
    return {
        "status": "healthy",
        "service": settings.service_name,
        "rabbitmq": "connected" if is_consumer_running() else "disconnected"
    }