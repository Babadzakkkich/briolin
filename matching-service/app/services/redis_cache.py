import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import logger


class RedisCache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self):
        try:
            self.redis = redis.from_url(settings.redis.url, decode_responses=True)
            await self.redis.ping()
            self._connected = True
            logger.info("Redis cache connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._connected = False

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self._connected = False

    async def get(self, key: str) -> Optional[Any]:
        if not self._connected:
            return None
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        if not self._connected:
            return
        try:
            await self.redis.setex(key, ttl_seconds, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

    async def delete(self, key: str):
        if not self._connected:
            return
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")

    async def incr(self, key: str) -> int:
        if not self._connected:
            return 0
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.warning(f"Redis incr error: {e}")
            return 0

    async def expire(self, key: str, ttl_seconds: int):
        if not self._connected:
            return
        try:
            await self.redis.expire(key, ttl_seconds)
        except Exception as e:
            logger.warning(f"Redis expire error: {e}")


redis_cache = RedisCache()