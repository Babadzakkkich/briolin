import logging
import re
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket

from app.services.keycloak_client import keycloak_client
from app.services.auth_service_client import auth_service_client
from app.services.token_cache import get_token_cache
from shared.auth.jwt import jwt_manager
from shared.auth.security import request_security
from shared.auth.config import settings as shared_settings
from app.core.exceptions import AuthenticationException
from app.core.logger import logger

# Публичные эндпоинты (не требующие аутентификации)
PUBLIC_ENDPOINTS = [
    re.compile(r'^/api/v1/auth/(register|login|refresh|validate)$'),
    re.compile(r'^/health$'),
    re.compile(r'^/$'),
    re.compile(r'^/docs.*$'),
    re.compile(r'^/redoc.*$'),
    re.compile(r'^/openapi\.json$'),
    re.compile(r'^/ws/stats$'),  # Статистика WebSocket публична
]

# WebSocket эндпоинты (требуют специальной обработки)
WS_ENDPOINTS = [
    re.compile(r'^/ws$'),
    re.compile(r'^/ws/.*$'),
]


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.token_cache = get_token_cache()
        self.locks = {}
        self.lock_cleanup_interval = 300
        self.last_lock_cleanup = datetime.utcnow()
    
    async def _get_lock(self, keycloak_id: str) -> asyncio.Lock:
        """Получает или создает lock для пользователя"""
        await self._cleanup_old_locks()
        
        if keycloak_id not in self.locks:
            self.locks[keycloak_id] = asyncio.Lock()
        
        return self.locks[keycloak_id]
    
    async def _cleanup_old_locks(self):
        """Очищает старые locks"""
        now = datetime.utcnow()
        if (now - self.last_lock_cleanup).total_seconds() > self.lock_cleanup_interval:
            self.locks = {}
            self.last_lock_cleanup = now
            logger.debug("Cleaned up locks cache")
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Проверяет, является ли эндпоинт публичным"""
        return any(pattern.match(path) for pattern in PUBLIC_ENDPOINTS)
    
    def _is_websocket_endpoint(self, path: str) -> bool:
        """Проверяет, является ли эндпоинт WebSocket"""
        return any(pattern.match(path) for pattern in WS_ENDPOINTS)
    
    async def _extract_existing_token(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """Извлекает существующий токен из заголовков"""
        existing_token = None
        existing_signature = None
        
        for key, value in request.scope["headers"]:
            if key == b"x-internal-token":
                existing_token = value.decode()
            elif key == b"x-token-signature":
                existing_signature = value.decode()
        
        return existing_token, existing_signature
    
    async def _get_cached_token(self, keycloak_id: str) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Получает токен из Redis кэша"""
        try:
            cached_data = await self.token_cache.get_token(keycloak_id)
            if cached_data:
                token = cached_data.get("token")
                signature = cached_data.get("signature")
                user_data = cached_data.get("user_data")
                
                if token and jwt_manager.is_token_valid(token):
                    logger.debug(f"Found valid token in Redis cache for {keycloak_id}")
                    return token, signature, user_data
                else:
                    await self.token_cache.delete_token(keycloak_id)
                    logger.debug(f"Removed invalid token from Redis cache for {keycloak_id}")
        
        except Exception as e:
            logger.warning(f"Error getting token from Redis cache: {e}")
        
        return None, None, None
    
    async def _create_new_token(self, keycloak_id: str, token_info: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        """Создает новый внутренний токен"""
        user_details = await auth_service_client.get_user_details(keycloak_id)
        
        if not user_details:
            logger.error(f"User {keycloak_id} not found in services")
            raise AuthenticationException("User not found")
        
        internal_user_data = {
            "keycloak_id": keycloak_id,
            "id": user_details.get("id"),
            "username": token_info.get("preferred_username", user_details.get("username", "")),
            "email": token_info.get("email", user_details.get("email", "")),
            "roles": user_details.get("roles", []),
            "is_active": user_details.get("is_active", True),
            "is_test_passed": user_details.get("is_test_passed", False),
            "authenticated_at": datetime.utcnow().isoformat()
        }
        
        if not internal_user_data["roles"]:
            logger.warning(f"User {keycloak_id} has no roles assigned")
        
        internal_token = jwt_manager.create_internal_token(internal_user_data)
        signature = request_security.create_signature(internal_token)
        
        try:
            await self.token_cache.set_token(
                keycloak_id=keycloak_id,
                token=internal_token,
                signature=signature,
                user_data=internal_user_data,
                expires_minutes=shared_settings.shared.jwt_expire_minutes
            )
            logger.debug(f"Token cached in Redis for {keycloak_id}")
        except Exception as e:
            logger.warning(f"Failed to cache token in Redis: {e}")
        
        logger.info(f"Created NEW internal token for user: {internal_user_data['username']}")
        
        token_info = jwt_manager.get_token_info(internal_token)
        if token_info.get("time_left_seconds"):
            logger.debug(
                f"Token expires in {token_info['time_left_seconds']:.0f} seconds "
                f"(at {token_info.get('expires_at').strftime('%H:%M:%S')})"
            )
        
        return internal_token, signature, internal_user_data
    
    async def _validate_existing_token(
        self, 
        existing_token: str, 
        existing_signature: str, 
        keycloak_id: str
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Проверяет существующий токен из заголовков запроса"""
        if not existing_token or not existing_signature:
            return None, None, None
        
        if not request_security.verify_signature(existing_token, existing_signature):
            logger.debug("Existing token signature invalid")
            return None, None, None
        
        token_info = jwt_manager.get_token_info(existing_token)
        if not token_info.get("valid", False):
            reason = "expired" if token_info.get("expired") else "invalid"
            logger.debug(f"Existing token {reason}")
            return None, None, None
        
        if token_info.get("keycloak_id") != keycloak_id:
            logger.debug(
                f"Existing token for different user: "
                f"expected {keycloak_id[:8]}..., got {token_info.get('keycloak_id', '')[:8]}..."
            )
            return None, None, None
        
        try:
            payload = jwt_manager.decode_internal_token(existing_token, verify_exp=False)
            user_data = payload.get("user", {})
            
            time_left = token_info.get("time_left_seconds", 0)
            logger.debug(
                f"Reusing EXISTING valid token for user: {user_data.get('username')}. "
                f"Time left: {time_left:.0f} seconds"
            )
            
            return existing_token, existing_signature, user_data
        except Exception as e:
            logger.debug(f"Error decoding existing token: {e}")
            return None, None, None
    
    async def _get_or_create_token(
        self, 
        keycloak_id: str, 
        token_info: Dict[str, Any],
        existing_token: Optional[str] = None,
        existing_signature: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Получает существующий или создает новый токен"""
        if existing_token and existing_signature:
            token, signature, user_data = await self._validate_existing_token(
                existing_token, existing_signature, keycloak_id
            )
            if token:
                return token, signature, user_data
        
        token, signature, user_data = await self._get_cached_token(keycloak_id)
        if token:
            return token, signature, user_data
        
        logger.debug(f"Creating new internal token for {keycloak_id}")
        return await self._create_new_token(keycloak_id, token_info)
    
    async def dispatch(self, request: Request, call_next):
        """
        Основной метод middleware.
        Обрабатывает HTTP запросы и WebSocket upgrade запросы.
        """
        path = request.url.path
        method = request.method

        if method == "OPTIONS":
            logger.debug(f"Preflight request: {path}")
            return await call_next(request)

        is_public = self._is_public_endpoint(path)
        is_websocket = self._is_websocket_endpoint(path)

        # Логируем каждый запрос
        logger.info(f"Incoming request: {method} {path}")
        if logger.isEnabledFor(logging.DEBUG):
            auth_headers = {}
            for key, value in request.headers.items():
                if key.lower().startswith(('authorization', 'x-internal', 'x-token')):
                    if 'token' in key.lower() and len(value) > 30:
                        auth_headers[key] = f"{value[:30]}..."
                    else:
                        auth_headers[key] = value
            if auth_headers:
                logger.debug(f"Auth headers: {auth_headers}")

        if is_public:
            logger.debug(f"Public endpoint accessed: {path}")
            return await call_next(request)

        # Для WebSocket эндпоинтов проверяем токен, но не требуем его в заголовках
        # (токен может быть в query параметрах)
        if is_websocket:
            logger.debug(f"WebSocket endpoint detected: {path}")
            # WebSocket аутентификация обрабатывается в самом эндпоинте
            # или через query параметры
            return await call_next(request)

        # Стандартная HTTP аутентификация
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"}
            )

        token = auth_header.split(" ")[1]
        logger.debug(f"Authorization token received: {token[:10]}... (truncated)")

        try:
            # 1. Валидируем токен через Keycloak
            token_info = keycloak_client.introspect_token(token)
            keycloak_id = token_info.get("sub")
            logger.debug(f"Keycloak ID: {keycloak_id[:8]}...")

            # 2. Извлекаем существующий токен из заголовков
            existing_token, existing_signature = await self._extract_existing_token(request)

            # 3. Используем lock для предотвращения race condition
            lock = await self._get_lock(keycloak_id)
            async with lock:
                # 4. Получаем или создаем токен
                internal_token, signature, user_data = await self._get_or_create_token(
                    keycloak_id=keycloak_id,
                    token_info=token_info,
                    existing_token=existing_token,
                    existing_signature=existing_signature
                )

                # 5. Сохраняем данные в request.state
                request.state.user = user_data
                request.state.internal_token = internal_token
                request.state.token_signature = signature

                # 6. Обновляем заголовки запроса
                new_headers = []
                for key, value in request.scope["headers"]:
                    key_lower = key.lower()
                    if key_lower not in [b"authorization", b"x-internal-token", b"x-token-signature"]:
                        new_headers.append((key, value))
                new_headers.append((b"x-internal-token", internal_token.encode()))
                new_headers.append((b"x-token-signature", signature.encode()))
                request.scope["headers"] = new_headers

                # 7. Логируем результат аутентификации
                token_info = jwt_manager.get_token_info(internal_token)
                time_left = token_info.get("time_left_seconds", 0)
                logger.info(
                    f"Authenticated user: {user_data['username']} "
                    f"(roles: {user_data['roles']}, "
                    f"token expires in: {time_left:.0f}s)"
                )

            return await call_next(request)

        except AuthenticationException as e:
            logger.warning(f"Authentication failed: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unexpected auth error: {e}", exc_info=True)
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )