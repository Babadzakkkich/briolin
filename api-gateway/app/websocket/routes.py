from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status, Query
from typing import Optional
import asyncio

from app.core.logger import logger
from app.websocket.proxy import get_websocket_proxy, WebSocketProxy
from app.services.token_cache import get_token_cache
from shared.auth.jwt import jwt_manager
from shared.auth.security import request_security

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Keycloak access token"),
):
    """
    WebSocket эндпоинт для чатов.
    
    Принимает Keycloak токен в query параметре ?token= или 
    в заголовке Authorization (обрабатывается middleware).
    
    Проксирует соединение к chat-service:9000/ws с internal JWT токеном.
    """
    await websocket.accept()
    
    # Получаем токен из query или из state (установлен middleware)
    keycloak_token = token
    
    # Проверяем, есть ли уже internal токен от middleware
    internal_token = getattr(websocket.state, "internal_token", None)
    token_signature = getattr(websocket.state, "token_signature", None)
    user_data = getattr(websocket.state, "user", None)
    
    # Если middleware не установил токен, проверяем query параметр
    if not internal_token and keycloak_token:
        # Валидируем Keycloak токен и создаем internal токен
        from app.services.keycloak_client import keycloak_client
        
        try:
            # Валидируем токен через Keycloak
            token_info = keycloak_client.introspect_token(keycloak_token)
            keycloak_id = token_info.get("sub")
            
            if not keycloak_id:
                await _send_auth_error(websocket, "Invalid token: no subject")
                return
            
            # Получаем данные пользователя
            from app.services.auth_service_client import auth_service_client
            user_details = await auth_service_client.get_user_details(keycloak_id)
            
            if not user_details:
                await _send_auth_error(websocket, "User not found")
                return
            
            # Создаем internal данные пользователя
            user_data = {
                "keycloak_id": keycloak_id,
                "id": user_details.get("id"),
                "username": token_info.get("preferred_username", user_details.get("username", "")),
                "email": token_info.get("email", user_details.get("email", "")),
                "roles": user_details.get("roles", []),
                "is_active": user_details.get("is_active", True),
                "is_test_passed": user_details.get("is_test_passed", False),
                "authenticated_at": __import__('datetime').datetime.utcnow().isoformat()
            }
            
            # Проверяем активность
            if not user_data["is_active"]:
                await _send_auth_error(websocket, "User is not active")
                return
            
            # Создаем internal токен
            internal_token = jwt_manager.create_internal_token(user_data)
            token_signature = request_security.create_signature(internal_token)
            
            # Кэшируем токен
            try:
                token_cache = get_token_cache()
                await token_cache.set_token(
                    keycloak_id=keycloak_id,
                    token=internal_token,
                    signature=token_signature,
                    user_data=user_data,
                    expires_minutes=5
                )
            except Exception as e:
                logger.warning(f"Failed to cache WebSocket token: {e}")
            
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await _send_auth_error(websocket, "Authentication failed")
            return
    
    # Проверяем, что аутентификация успешна
    if not internal_token or not user_data:
        await _send_auth_error(websocket, "Authentication required")
        return
    
    # Получаем прокси и проксируем соединение
    proxy = get_websocket_proxy()
    await proxy.handle_connection(
        websocket=websocket,
        user_data=user_data,
        internal_token=internal_token,
        token_signature=token_signature
    )


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Получить статистику WebSocket соединений (для мониторинга)
    """
    proxy = get_websocket_proxy()
    return proxy.get_stats()


async def _send_auth_error(websocket: WebSocket, message: str):
    """Отправляет ошибку аутентификации и закрывает соединение"""
    import json
    from datetime import datetime
    
    error_msg = {
        "type": "error",
        "message": {"error": message, "code": "AUTHENTICATION_FAILED"},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        await websocket.send_text(json.dumps(error_msg))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        logger.debug(f"Error sending auth error: {e}")