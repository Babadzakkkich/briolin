from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import ProfileServiceException
from app.core.exception_handlers import profile_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer
from app.consumers import register_consumers
from app.services.saga_worker import get_saga_worker
from app.services.saga_handlers import ProfileSagaHandlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Profile Service...")
    
    # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Создаем таблицы для саги
        from shared.saga.models import SagaBase
        await conn.run_sync(SagaBase.metadata.create_all)
    
    # Подключение к RabbitMQ
    rabbitmq_connected = False
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()
        
        # Регистрация consumers
        await register_consumers()
        
        rabbitmq_connected = True
        logger.info("Profile Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
    
    # Инициализация и запуск SAGA воркера
    try:
        saga_worker = get_saga_worker()
        
        # Регистрируем обработчики шагов
        handlers = ProfileSagaHandlers()

        # Основные шаги
        saga_worker.register_step_handler("create_basic_profile", handlers.handle_create_basic_profile)
        saga_worker.register_step_handler("create_detailed_profile", handlers.handle_create_detailed_profile)
        saga_worker.register_step_handler("update_basic_profile", handlers.handle_update_basic_profile)
        saga_worker.register_step_handler("update_detailed_profile", handlers.handle_update_detailed_profile)
        saga_worker.register_step_handler("delete_basic_profile", handlers.handle_delete_basic_profile)

        # Шаги публикации событий
        saga_worker.register_step_handler("publish_profile_created", handlers.handle_publish_profile_created)
        saga_worker.register_step_handler("publish_profile_updated", handlers.handle_publish_profile_updated)
        saga_worker.register_step_handler("publish_profile_deleted", handlers.handle_publish_profile_deleted)

        # Компенсации
        saga_worker.register_step_handler("compensate_create_basic_profile", handlers.handle_compensate_create_basic_profile)
        
        # Запускаем воркер
        await saga_worker.start()
        logger.info("SAGA Worker started")
    except Exception as e:
        logger.error(f"Failed to start SAGA worker: {e}")
        
    # Проверяем наличие моделей в кэше
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    models = [
        "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
        "models--blanchefort--rubert-base-cased-sentiment"
    ]
    
    for model in models:
        model_path = os.path.join(cache_dir, model)
        if os.path.exists(model_path):
            logger.info(f"Model cached: {model}")
        else:
            logger.info(f"Model not cached (will download on first use): {model}")

    
    yield
    
    logger.info("Shutting down Profile Service...")
    
    # Остановка SAGA воркера
    try:
        saga_worker = get_saga_worker()
        await saga_worker.stop()
        logger.info("SAGA Worker stopped")
    except Exception as e:
        logger.error(f"Error stopping SAGA worker: {e}")
    
    # Отключение от RabbitMQ
    if rabbitmq_connected:
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
    saga_worker = get_saga_worker()
    return {
        "status": "healthy",
        "service": settings.service_name,
        "rabbitmq": "connected" if rabbitmq_publisher._is_connected else "disconnected",
        "saga_worker": "running" if saga_worker._running else "stopped"
    }