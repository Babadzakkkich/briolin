from typing import AsyncGenerator, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)

# Keycloak клиент будет подключен через API Gateway
# В этом сервисе мы только валидируем токен через публичный эндпоинт Keycloak

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Получение текущего пользователя из заголовков Gateway"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    
    try:
        # Gateway должен передавать информацию о пользователе в заголовках
        # Но для совместимости пока валидируем токен самостоятельно
        
        # TODO: В будущем Gateway будет передавать X-User-Info
        # Пока возвращаем минимальную информацию
        
        return {
            "id": "user-id-from-token",  # Временно
            "keycloak_id": "keycloak-id-from-token",  # Временно
            "roles": ["user"]  # Временно
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

async def require_role(role: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Декоратор для проверки роли"""
    if role not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {role} required"
        )
    return current_user