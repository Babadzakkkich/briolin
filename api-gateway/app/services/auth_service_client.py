import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.core.logger import logger


class AuthServiceClient:
    """
    Клиент для взаимодействия с auth-service
    С кэшированием для уменьшения нагрузки
    """
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.auth_service_url = settings.services.auth
        self.redis_client = None
        
        # In-memory кэш на случай если Redis недоступен
        self.memory_cache = {}
    
    async def _get_redis(self):
        """Ленивая инициализация Redis"""
        if self.redis_client is None and settings.cache.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.cache.redis_url,
                    decode_responses=True
                )
                logger.info("Redis client initialized")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        
        return self.redis_client
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Получение данных из кэша"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                data = await redis_client.get(key)
                if data:
                    return json.loads(data)
            
            # Fallback to memory cache
            if key in self.memory_cache:
                cached_item = self.memory_cache[key]
                if datetime.now() < cached_item["expires"]:
                    return cached_item["data"]
                else:
                    del self.memory_cache[key]
        
        except Exception as e:
            logger.warning(f"Cache error: {e}")
        
        return None
    
    async def _set_to_cache(self, key: str, data: Dict[str, Any], ttl: int):
        """Сохранение данных в кэш"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                await redis_client.setex(
                    key,
                    ttl,
                    json.dumps(data)
                )
            else:
                # Fallback to memory cache
                self.memory_cache[key] = {
                    "data": data,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
                
                # Очистка старых записей
                expired_keys = [
                    k for k, v in self.memory_cache.items()
                    if datetime.now() >= v["expires"]
                ]
                for k in expired_keys:
                    del self.memory_cache[k]
        
        except Exception as e:
            logger.warning(f"Cache error: {e}")
    
    async def get_user_details(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о пользователе из auth-service
        С кэшированием на 1 минуту
        """
        cache_key = f"user:{keycloak_id}"
        
        # Пробуем получить из кэша
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"User {keycloak_id} retrieved from cache")
            return cached_data
        
        try:
            # Запрос к auth-service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/users/keycloak/{keycloak_id}",
                    headers={"x-internal-request": "true"}  # Специальный заголовок
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    
                    # Сохраняем в кэш
                    await self._set_to_cache(
                        cache_key,
                        user_data,
                        settings.cache.user_cache_ttl
                    )
                    
                    logger.debug(f"User {keycloak_id} retrieved from auth-service")
                    return user_data
                elif response.status_code == 404:
                    logger.warning(f"User {keycloak_id} not found in auth-service")
                    return None
                else:
                    logger.error(f"Auth service error: {response.status_code}")
                    raise ServiceUnavailableException("auth-service")
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to auth-service at {self.auth_service_url}")
            raise ServiceUnavailableException("auth-service")
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            raise ServiceUnavailableException("auth-service")
    
    async def validate_user_active(self, keycloak_id: str) -> bool:
        """Проверка активности пользователя"""
        user_details = await self.get_user_details(keycloak_id)
        return bool(user_details and user_details.get("is_active", False))


# Синглтон экземпляр
auth_service_client = AuthServiceClient()