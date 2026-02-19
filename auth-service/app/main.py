from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import AuthException
from app.core.exception_handlers import auth_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.rabbitmq import rabbitmq_publisher, rabbitmq_consumer
from app.consumers import register_consumers
from app.services.saga_worker import get_saga_worker
from app.services.saga_handlers import AuthSagaHandlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    
    # Инициализация БД
    async with engine.begin() as conn:
        # Создаем основные таблицы
        await conn.run_sync(Base.metadata.create_all)
        
        # Создаем таблицы для саги
        from shared.saga.models import SagaBase
        await conn.run_sync(SagaBase.metadata.create_all)
    
    # Подключение к RabbitMQ
    rabbitmq_connected = False
    try:
        await rabbitmq_publisher.connect()
        await rabbitmq_consumer.connect()
        rabbitmq_connected = True
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
    
    # Регистрация consumers (если RabbitMQ доступен)
    if rabbitmq_connected:
        try:
            await register_consumers()
            logger.info("Consumers registered")
        except Exception as e:
            logger.error(f"Failed to register consumers: {e}")
    
    # Инициализация и запуск SAGA воркера
    try:
        saga_worker = get_saga_worker()
        
        # Регистрируем обработчики шагов
        handlers = AuthSagaHandlers()

        # Основные шаги
        saga_worker.register_step_handler("create_keycloak_user", handlers.handle_create_keycloak_user)
        saga_worker.register_step_handler("create_auth_db_user", handlers.handle_create_auth_db_user)
        saga_worker.register_step_handler("update_keycloak_user", handlers.handle_update_keycloak_user)
        saga_worker.register_step_handler("update_auth_db_user", handlers.handle_update_auth_db_user)
        saga_worker.register_step_handler("delete_keycloak_user", handlers.handle_delete_keycloak_user)
        saga_worker.register_step_handler("delete_auth_db_user", handlers.handle_delete_auth_db_user)

        # Шаги публикации событий
        saga_worker.register_step_handler("publish_user_registered", handlers.handle_publish_user_registered)
        saga_worker.register_step_handler("publish_user_profile_updated", handlers.handle_publish_user_profile_updated)
        saga_worker.register_step_handler("publish_user_status_changed", handlers.handle_publish_user_status_changed)
        saga_worker.register_step_handler("publish_user_roles_updated", handlers.handle_publish_user_roles_updated)
        saga_worker.register_step_handler("publish_user_deleted", handlers.handle_publish_user_deleted)

        # Компенсации
        saga_worker.register_step_handler("compensate_create_keycloak_user", handlers.handle_compensate_create_keycloak_user)
        saga_worker.register_step_handler("compensate_create_auth_db_user", handlers.handle_compensate_create_auth_db_user)
        
        # Запускаем воркер
        await saga_worker.start()
        logger.info("SAGA Worker started")
    except Exception as e:
        logger.error(f"Failed to start SAGA worker: {e}")
    
    logger.info("Auth Service started successfully")
    
    yield
    
    logger.info("Shutting down Auth Service...")
    
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
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    await dispose_engine()
    logger.info("Auth Service shutdown complete")

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(AuthException, auth_exception_handler)
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