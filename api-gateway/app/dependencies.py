from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List

from app.core.exceptions import AuthenticationException, AuthorizationException

# Эти зависимости больше НЕ ИСПОЛЬЗУЮТСЯ в роутах API Gateway
# Они остаются для совместимости, но реальная проверка в middleware

# Схема безопасности
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Совместимость - получаем из request.state"""
    if not hasattr(request.state, 'user'):
        raise AuthenticationException("User not authenticated")
    return request.state.user

def require_role(role: str):
    """Декоратор для проверки realm роли"""
    async def role_checker(
        user: Dict[str, Any] = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        user_roles = user.get("roles", [])
        if role not in user_roles:
            raise AuthorizationException(f"Role '{role}' is required")
        return user
    return role_checker

def require_any_role(roles: List[str]):
    """Декоратор для проверки любой из realm ролей"""
    async def role_checker(
        user: Dict[str, Any] = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise AuthorizationException(f"One of roles {roles} is required")
        return user
    return role_checker