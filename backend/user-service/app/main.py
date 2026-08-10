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
from app.services.saga_worker import get_saga_worker
from app.services.saga_handlers import UserSagaHandlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting User Service...")
    
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
        logger.info("User Service publisher connected to RabbitMQ")
        
        await rabbitmq_consumer.connect()
        logger.info("User Service consumer connected to RabbitMQ")
        
        rabbitmq_connected = True
        
        # Регистрация consumers
        await register_consumers()
        
        logger.info("User Service started successfully with RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
    
    # Инициализация и запуск SAGA воркера
    try:
        saga_worker = get_saga_worker()
        
        # Регистрируем обработчики шагов
        handlers = UserSagaHandlers()

        # Основные шаги
        saga_worker.register_step_handler("create_user_profile", handlers.handle_create_user_profile)
        saga_worker.register_step_handler("assign_user_role", handlers.handle_assign_user_role)
        saga_worker.register_step_handler("update_user_profile", handlers.handle_update_user_profile)
        saga_worker.register_step_handler("update_user_roles", handlers.handle_update_user_roles)
        saga_worker.register_step_handler("delete_user_profile", handlers.handle_delete_user_profile)

        saga_worker.register_step_handler("publish_user_profile_update_requested", handlers.handle_publish_user_profile_update_requested)
        saga_worker.register_step_handler("publish_user_status_change_requested", handlers.handle_publish_user_status_change_requested)
        saga_worker.register_step_handler("publish_user_roles_update_requested", handlers.handle_publish_user_roles_update_requested)
        saga_worker.register_step_handler("publish_user_deletion_requested", handlers.handle_publish_user_deletion_requested)

        # Шаги публикации подтверждений
        saga_worker.register_step_handler("publish_user_profile_created", handlers.handle_publish_user_profile_created)
        saga_worker.register_step_handler("publish_user_updated", handlers.handle_publish_user_updated)
        saga_worker.register_step_handler("publish_user_roles_updated", handlers.handle_publish_user_roles_updated)
        saga_worker.register_step_handler("publish_user_deleted", handlers.handle_publish_user_deleted)

        # Компенсации
        saga_worker.register_step_handler("compensate_create_user_profile", handlers.handle_compensate_create_user_profile)
        saga_worker.register_step_handler("compensate_assign_user_role", handlers.handle_compensate_assign_user_role)
        
        # Запускаем воркер
        await saga_worker.start()
        logger.info("SAGA Worker started")
    except Exception as e:
        logger.error(f"Failed to start SAGA worker: {e}")
    
    yield
    
    logger.info("Shutting down User Service...")
    
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
app.add_exception_handler(UserServiceException, user_exception_handler)
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
    saga_worker = get_saga_worker()
    return {
        "status": "healthy",
        "service": settings.service_name,
        "rabbitmq": "connected" if rabbitmq_publisher._is_connected else "disconnected",
        "saga_worker": "running" if saga_worker._running else "stopped"
    }