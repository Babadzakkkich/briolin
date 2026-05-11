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
from app.schemas.verify import VerifyConfirmRequest, RequestCodeRequest, PasswordResetRequest, PasswordResetConfirmRequest
from app.core.logger import logger
import httpx
from pydantic import BaseModel
import json

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


# ========== ВЕРИФИКАЦИЯ EMAIL ==========

@router.post("/verify/request")
async def request_verification_code(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Запросить код верификации на email.
    Требует авторизации.
    """ 
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post("/verify/confirm")
async def verify_email_code(
    confirm_data: VerifyConfirmRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Подтвердить email по коду.
    Требует авторизации.
    """    
    request._body = json.dumps({"code": confirm_data.code}).encode()
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    request_obj: Request
):
    """
    Запросить сброс пароля — отправить код на email.
    Публичный эндпоинт.
    """
    request_obj._body = json.dumps({"email": request.email}).encode()
    response = await http_client.proxy_request(request_obj)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    request_obj: Request
):
    """
    Подтвердить сброс пароля — проверить код и установить новый пароль.
    Публичный эндпоинт.
    """
    request_obj._body = json.dumps({
        "email": request.email,
        "code": request.code,
        "new_password": request.new_password
    }).encode()
    response = await http_client.proxy_request(request_obj)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )