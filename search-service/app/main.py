from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import SearchServiceException
from app.core.exception_handlers import search_exception_handler, global_exception_handler
from app.api.v1 import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}...")

    # Инициализация БД
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    logger.info(f"Shutting down {settings.app_name}...")
    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    description="API для классического и таргетированного поиска по профилям пользователей",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Регистрируем обработчики исключений
app.add_exception_handler(SearchServiceException, search_exception_handler)
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
    """
    Health check endpoint для мониторинга
    """
    # Проверяем соединение с БД
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    return {
        "status": "healthy",
        "service": settings.service_name,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "debug_mode": settings.debug
    }

@app.get("/")
async def root():
    """
    Корневой эндпоинт с информацией о сервисе
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "service": settings.service_name,
        "endpoints": {
            "classic_search": "/api/v1/search/classic",
            "targeted_search": "/api/v1/search/targeted",
            "history": "/api/v1/search/history",
            "session": "/api/v1/search/session/{session_id}",
            "profiles_count": "/api/v1/search/profiles/count",
            "lock_status": "/api/v1/search/lock-status",
            "health": "/health",
            "docs": "/docs"
        }
    }