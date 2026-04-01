from typing import Dict, Any
from fastapi import Depends, HTTPException, Request

from .jwt import jwt_manager


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Получение текущего пользователя из внутреннего JWT токена"""
    internal_token = request.headers.get("x-internal-token")
    if not internal_token:
        raise HTTPException(
            status_code=401,
            detail="Missing internal authentication token"
        )
    
    payload = jwt_manager.decode_internal_token(internal_token)
    user_data = payload.get("user", {})
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid user data in token")
    
    return user_data


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Проверка, что пользователь активен"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User is not active")
    return current_user


def require_role(role: str):
    """Декоратор для проверки роли пользователя"""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if role not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' is required"
            )
        return current_user
    return role_checker


def require_any_role(roles: list[str]):
    """Декоратор для проверки любой из указанных ролей"""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=403,
                detail=f"One of roles {roles} is required"
            )
        return current_user
    return role_checker


def require_test_passed():
    """
    Декоратор для проверки, что пользователь прошел тест
    """
    async def test_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not current_user.get("is_test_passed", False):
            raise HTTPException(
                status_code=403,
                detail="Test not passed. Please complete the test first."
            )
        return current_user
    return test_checker

def require_admin():
    async def admin_checker(current_user: dict = Depends(get_current_user)):
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        return current_user
    return admin_checker