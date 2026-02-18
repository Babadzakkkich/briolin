from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logger import logger

_mongo_client = None
_mongo_db = None

async def get_mongo_client() -> AsyncIOMotorClient:
    """Получение MongoDB клиента"""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = AsyncIOMotorClient(
                settings.mongo.url,
                maxPoolSize=10,
                minPoolSize=1
            )
            await _mongo_client.admin.command('ping')
            logger.info("MongoDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return _mongo_client

async def get_mongo_db() -> AsyncIOMotorDatabase:
    """Получение MongoDB базы данных"""
    global _mongo_db
    if _mongo_db is None:
        client = await get_mongo_client()
        _mongo_db = client[settings.mongo.database]
    return _mongo_db

async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB connection closed")