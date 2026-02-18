from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engines, init_db
from app.core.exceptions import SearchServiceException
from app.core.exception_handlers import search_exception_handler, global_exception_handler
from app.api.v1.search import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}...")

    # Инициализация БД (создание таблиц только в своей БД)
    if settings.debug:
        await init_db()
        logger.info("Database tables initialized in own database")

    yield

    logger.info(f"Shutting down {settings.app_name}...")

    # Закрытие соединений с обеими БД
    await dispose_engines()


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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API роуты
app.include_router(search_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "endpoints": {
            "classic_search": "/api/v1/search/classic/{user_id}",
            "targeted_search": "/api/v1/search/targeted/{user_id}",
            "history": "/api/v1/search/history/{user_id}",
            "session": "/api/v1/search/session/{session_id}",
            "profiles_count": "/api/v1/search/profiles/count",
            "lock_status": "/api/v1/search/lock-status/{user_id}",
            "docs": "/docs"
        }
    }