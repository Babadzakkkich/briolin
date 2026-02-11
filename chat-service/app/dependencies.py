from typing import Optional, AsyncGenerator
from fastapi import Depends, WebSocket, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.jwt import jwt_manager
from shared.auth.dependencies import get_current_user as shared_get_current_user
from app.database.postgres.session import async_session_factory
from app.services.chat_service import ChatService
from app.core.logger import logger
from app.services.profile_service_client import get_profile_service_client

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии БД"""
    async with async_session_factory() as session:
        yield session

def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Зависимость для получения ChatService"""
    return ChatService(db)

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> Optional[dict]:
    """Получение текущего пользователя для WebSocket"""
    if not token:
        logger.warning("No token provided for WebSocket connection")
        return None
    
    try:
        # Проверяем токен
        payload = jwt_manager.decode_internal_token(token)
        user_data = payload.get("user", {})
        
        if not user_data:
            logger.warning("No user data in token for WebSocket")
            return None
        
        # Обогащаем данные пользователя display_name из profile-service
        try:
            profile_client = get_profile_service_client()
            keycloak_id = user_data.get("keycloak_id")
            if keycloak_id:
                display_name = await profile_client.get_display_name(keycloak_id)
                user_data["display_name"] = display_name
        except Exception as e:
            logger.warning(f"Failed to get display_name for WebSocket user: {e}")
        
        return user_data
        
    except Exception as e:
        logger.warning(f"Failed to authenticate WebSocket: {e}")
        return None

# Реэкспорт shared зависимостей
from shared.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_any_role,
    require_test_passed
)

__all__ = [
    'get_db',
    'get_chat_service',
    'get_current_user_ws',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role',
    'require_test_passed'
]