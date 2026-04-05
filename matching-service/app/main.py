from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.database.session import dispose_engine, engine
from app.database.models import Base
from app.core.exceptions import MatchingServiceException
from app.core.exception_handlers import matching_exception_handler, global_exception_handler
from app.api.v1 import router as api_router
from app.services.redis_cache import redis_cache
from app.services.rabbitmq import event_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Matching Service...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Connect to Redis
    await redis_cache.connect()

    # Connect to RabbitMQ
    try:
        await event_publisher.connect()
        logger.info("RabbitMQ connected")
    except Exception as e:
        logger.error(f"RabbitMQ connection failed: {e}")

    yield

    logger.info("Shutting down Matching Service...")
    await event_publisher.disconnect()
    await redis_cache.disconnect()
    await dispose_engine()


app = FastAPI(
    title="Briolin Matching Service",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

app.add_exception_handler(MatchingServiceException, matching_exception_handler)
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
    return {
        "status": "healthy",
        "service": settings.service_name,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    return {
        "service": "matching-service",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else None
    }