import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import logger


class TokenCache:
    """Кэш для внутренних JWT токенов с использованием Redis"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self._lock = asyncio.Lock()
        self.connection_attempts = 0
        self.max_connection_attempts = 3
    
    async def _ensure_connection(self):
        """Обеспечивает подключение к Redis"""
        async with self._lock:
            if self.redis_client is None and self.connection_attempts < self.max_connection_attempts:
                try:
                    self.redis_client = redis.from_url(
                        self.redis_url,
                        decode_responses=True,
                        socket_connect_timeout=2,
                        socket_timeout=2,
                        retry_on_timeout=True,
                        max_connections=10
                    )
                    # Проверяем соединение
                    await self.redis_client.ping()
                    logger.info("Token cache Redis client initialized successfully")
                    self.connection_attempts = 0
                except Exception as e:
                    logger.error(f"Failed to connect to Redis for token cache: {e}")
                    self.redis_client = None
                    self.connection_attempts += 1
                    
                    if self.connection_attempts >= self.max_connection_attempts:
                        logger.warning(
                            f"Max Redis connection attempts reached ({self.max_connection_attempts}). "
                            f"Token cache will be disabled."
                        )
        
        return self.redis_client
    
    async def get_token(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получает токен из Redis кэша"""
        client = await self._ensure_connection()
        if not client:
            return None
        
        try:
            # Используем pipeline для атомарности
            async with client.pipeline() as pipe:
                pipe.get(f"token:{keycloak_id}")
                pipe.ttl(f"token:{keycloak_id}")
                result = await pipe.execute()
            
            data = result[0]
            ttl = result[1]
            
            if data:
                token_data = json.loads(data)
                
                # Проверяем TTL
                if ttl > 0:
                    logger.debug(f"Token found in Redis cache for {keycloak_id[:8]}... (TTL: {ttl}s)")
                    return token_data
                else:
                    # TTL истек или отрицательный - удаляем
                    await client.delete(f"token:{keycloak_id}")
                    logger.debug(f"Expired token removed from Redis cache for {keycloak_id[:8]}...")
        
        except redis.RedisError as e:
            logger.warning(f"Redis error (get_token): {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for token {keycloak_id[:8]}...: {e}")
            await client.delete(f"token:{keycloak_id}")
        except Exception as e:
            logger.warning(f"Unexpected error in get_token: {e}")
        
        return None
    
    async def set_token(
        self, 
        keycloak_id: str, 
        token: str, 
        signature: str, 
        user_data: Dict[str, Any],
        expires_minutes: int
    ):
        """Сохраняет токен в Redis кэш"""
        client = await self._ensure_connection()
        if not client:
            return
        
        try:
            token_data = {
                "token": token,
                "signature": signature,
                "user_data": user_data,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=expires_minutes)).isoformat()
            }
            
            # Сохраняем с TTL (на 30 секунд больше, чем время жизни токена)
            ttl_seconds = expires_minutes * 60 + 30
            
            await client.setex(
                f"token:{keycloak_id}",
                ttl_seconds,
                json.dumps(token_data)
            )
            
            logger.debug(f"Token cached in Redis for {keycloak_id[:8]}... (TTL: {ttl_seconds}s)")
            
            # Также сохраняем обратное отображение token -> keycloak_id
            # (полезно для отладки и мониторинга)
            token_preview = token[:50] + "..." if len(token) > 53 else token
            await client.setex(
                f"token_map:{token_preview}",
                ttl_seconds,
                keycloak_id
            )
            
        except redis.RedisError as e:
            logger.warning(f"Redis error (set_token): {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in set_token: {e}")
    
    async def delete_token(self, keycloak_id: str):
        """Удаляет токен из Redis кэша"""
        client = await self._ensure_connection()
        if not client:
            return
        
        try:
            # Сначала получаем токен, чтобы удалить обратное отображение
            data = await client.get(f"token:{keycloak_id}")
            if data:
                token_data = json.loads(data)
                token = token_data.get("token", "")
                if token:
                    token_preview = token[:50] + "..." if len(token) > 53 else token
                    await client.delete(f"token_map:{token_preview}")
            
            # Удаляем основной ключ
            await client.delete(f"token:{keycloak_id}")
            logger.debug(f"Token deleted from Redis cache for {keycloak_id[:8]}...")
            
        except redis.RedisError as e:
            logger.warning(f"Redis error (delete_token): {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in delete_token: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получает статистику кэша"""
        client = await self._ensure_connection()
        if not client:
            return {"redis_available": False}
        
        try:
            # Ищем все ключи токенов
            keys = await client.keys("token:*")
            
            # Получаем информацию о каждом токене
            tokens_info = []
            for key in keys[:10]:  # Ограничиваем для производительности
                try:
                    data = await client.get(key)
                    if data:
                        token_data = json.loads(data)
                        ttl = await client.ttl(key)
                        
                        tokens_info.append({
                            "key": key,
                            "ttl": ttl,
                            "user": token_data.get("user_data", {}).get("username", "unknown"),
                            "created_at": token_data.get("created_at")
                        })
                except:
                    continue
            
            return {
                "redis_available": True,
                "total_tokens": len(keys),
                "sample_tokens": tokens_info
            }
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"redis_available": False, "error": str(e)}


# Глобальный экземпляр кэша
_token_cache = None

def get_token_cache() -> TokenCache:
    """Получает экземпляр кэша токенов (синглтон)"""
    global _token_cache
    
    if _token_cache is None:
        from app.core.config import settings
        _token_cache = TokenCache(settings.cache.redis_url)
        logger.info("Token cache instance created")
    
    return _token_cache