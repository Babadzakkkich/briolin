from fastapi import APIRouter, Request, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.http_client import http_client
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    RefreshRequest, 
    LogoutRequest, 
    UserResponse,
    TokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    request: Request
):
    """СИНХРОННАЯ регистрация нового пользователя"""
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
    refresh_data: RefreshRequest,
    request: Request
):
    """Обновление токена"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post("/logout")
async def logout_user(
    logout_data: LogoutRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Выход из системы"""
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
    """Валидация токена"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )