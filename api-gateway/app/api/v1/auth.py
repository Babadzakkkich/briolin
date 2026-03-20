from fastapi import APIRouter, Request, Response
from app.services.http_client import http_client
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    request: Request
):
    """Регистрация нового пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: UserLogin,
    request: Request
):
    """Аутентификация пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request
):
    """Обновление токена (refresh_token читается из httponly cookie)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post("/logout")
async def logout_user(
    request: Request
):
    """Выход из системы (refresh_token читается из httponly cookie)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post("/validate")
async def validate_token(
    request: Request
):
    """Валидация токена (для совместимости)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )