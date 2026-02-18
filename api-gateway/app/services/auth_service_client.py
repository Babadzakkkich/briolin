import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.core.logger import logger

class AuthServiceClient:
    """Клиент для взаимодействия с auth-service (внутренние эндпоинты)"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.auth_service_url = settings.services.auth
        self.user_service_url = settings.services.user  # ДОБАВЛЕНО
        self.redis_client = None
        self.memory_cache = {}
    
    async def _get_redis(self):
        """Ленивая инициализация Redis"""
        if self.redis_client is None and settings.cache.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.cache.redis_url,
                    decode_responses=True
                )
                logger.info("Redis client initialized for auth_service_client")
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
            
            # In-memory fallback
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
                await redis_client.setex(key, ttl, json.dumps(data))
            else:
                self.memory_cache[key] = {
                    "data": data,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
        except Exception as e:
            logger.warning(f"Cache error: {e}")
    
    async def get_user_details(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о пользователе из auth-service и user-service
        """
        cache_key = f"user:{keycloak_id}"
        
        # Пробуем получить из кэша
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"User {keycloak_id} retrieved from cache")
            return cached_data
        
        try:
            # 1. Получаем базовую информацию из auth-service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                auth_response = await client.get(
                    f"{self.auth_service_url}/api/v1/internal/users/{keycloak_id}",
                    headers={"x-internal-request": "true"}
                )
                
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    
                    # 2. Получаем расширенную информацию из user-service
                    user_response = await client.get(
                        f"{self.user_service_url}/api/v1/internal/users/{keycloak_id}",
                        headers={"x-internal-request": "true"}
                    )
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        
                        # Объединяем данные
                        combined_data = {
                            **auth_data,
                            **user_data
                        }
                        
                        await self._set_to_cache(cache_key, combined_data, settings.cache.user_cache_ttl)
                        logger.debug(f"User {keycloak_id} retrieved from both services")
                        return combined_data
                    elif user_response.status_code == 404:
                        logger.warning(f"User {keycloak_id} not found in user-service")
                        # Возвращаем только данные из auth-service
                        await self._set_to_cache(cache_key, auth_data, settings.cache.user_cache_ttl)
                        return auth_data
                    else:
                        logger.error(f"User service error: {user_response.status_code}")
                        # Возвращаем только данные из auth-service
                        await self._set_to_cache(cache_key, auth_data, settings.cache.user_cache_ttl)
                        return auth_data
                elif auth_response.status_code == 404:
                    logger.warning(f"User {keycloak_id} not found in auth-service")
                    return None
                else:
                    logger.error(f"Auth service error: {auth_response.status_code}")
                    raise ServiceUnavailableException("auth-service")
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to services")
            raise ServiceUnavailableException("services")
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            raise ServiceUnavailableException("services")
    
    async def validate_user_active(self, keycloak_id: str) -> bool:
        """Проверка активности пользователя"""
        user_details = await self.get_user_details(keycloak_id)
        return bool(user_details and user_details.get("is_active", False))

auth_service_client = AuthServiceClient()