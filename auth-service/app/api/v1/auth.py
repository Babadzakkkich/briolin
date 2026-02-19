from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.core.exceptions import UserAlreadyExistsException

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/saga/{saga_id}/status")
async def get_saga_status(
    saga_id: str,
    service: AuthService = Depends(get_auth_service)
):
    """Получение статуса регистрации по ID саги"""
    status = await service.get_saga_status(saga_id)
    return status

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Регистрация нового пользователя (публичный эндпоинт)"""
    response = await service.register(await request.json())
    return response

@router.post("/login")
async def login_user(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Аутентификация пользователя (публичный эндпоинт)"""
    response = await service.login(await request.json())
    return response

@router.post("/refresh")
async def refresh_token(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Обновление токена (публичный эндпоинт)"""
    response = await service.refresh_token(await request.json())
    return response

@router.post("/logout")
async def logout_user(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Выход из системы"""
    body = await request.json()
    response = await service.logout(body.get("refresh_token"))
    return response

@router.post("/validate")
async def validate_token(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Валидация токена (публичный эндпоинт - Gateway сам проверяет)"""
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token required"
        )
    
    response = await service.validate_token(token)
    return response