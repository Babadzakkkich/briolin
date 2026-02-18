from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import JSON
import json
from datetime import datetime
from decimal import Decimal

from app.core.config import settings

# PostgreSQL engine
postgres_engine = create_async_engine(
    settings.db.url,
    echo=settings.db.echo,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False, default=convert_for_json),
)

def convert_for_json(obj):
    """Конвертер для объектов, которые не могут быть сериализованы в JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

async_session_factory = async_sessionmaker(
    bind=postgres_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# MongoDB client
mongo_client = AsyncIOMotorClient(settings.mongo.url)
mongo_db = mongo_client[settings.mongo.database]

async def dispose_engine():
    await postgres_engine.dispose()

# Сокращенные имена для удобства
engine = postgres_engine
db = async_session_factory
mongo = mongo_db