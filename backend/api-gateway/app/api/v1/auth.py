import json
from typing import Optional

from fastapi import APIRouter, Request, Response, status, HTTPException
from fastapi.responses import JSONResponse

from app.services.http_client import http_client
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    SessionResponse,
)
from app.schemas.verify import (
    VerifyConfirmRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
)
from app.core.config import settings
from app.core.cookies import set_auth_cookies, clear_auth_cookies
from app.core.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _proxied_error_response(service_response) -> Response:
    return Response(
        content=service_response.content,
        status_code=service_response.status_code,
        media_type=service_response.headers.get("content-type", "application/json"),
    )


def _safe_json(service_response) -> dict:
    try:
        return service_response.json()
    except Exception:
        logger.warning("Service returned non-JSON auth response")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from auth service",
        )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    request: Request,
):
    """Регистрация нового пользователя. Публичный endpoint, CSRF не требуется."""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@router.post("/login", response_model=SessionResponse)
async def login_user(
    credentials: UserLogin,
    request: Request,
):
    """
    Аутентификация через HttpOnly cookies.

    auth-service возвращает Keycloak tokens во внутреннем ответе, gateway сохраняет
    их в HttpOnly cookies и наружу отдаёт только состояние сессии.
    """
    service_response = await http_client.proxy_request(request)

    if service_response.status_code >= 400:
        return _proxied_error_response(service_response)

    token_data = _safe_json(service_response)

    response = JSONResponse(
        content={
            "authenticated": True,
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
        }
    )
    set_auth_cookies(response, token_data)
    return response


@router.post("/refresh", response_model=SessionResponse)
async def refresh_token(
    request: Request,
):
    """Обновление access/refresh tokens через refresh_token из HttpOnly cookie."""
    refresh_token_value = request.cookies.get(settings.cookies.refresh_cookie_name)
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie not found",
        )

    # auth-service ожидает refresh_token в JSON body.
    request._body = json.dumps({"refresh_token": refresh_token_value}).encode("utf-8")

    service_response = await http_client.proxy_request(request)

    if service_response.status_code >= 400:
        response = JSONResponse(
            content={"detail": "Refresh failed"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        clear_auth_cookies(response)
        return response

    token_data = _safe_json(service_response)

    response = JSONResponse(
        content={
            "authenticated": True,
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
        }
    )
    set_auth_cookies(response, token_data)
    return response


@router.post("/logout")
async def logout_user(
    request: Request,
):
    """Выход из системы: отзывает refresh token в Keycloak и очищает cookies."""
    refresh_token_value = request.cookies.get(settings.cookies.refresh_cookie_name)

    if refresh_token_value:
        request._body = json.dumps({"refresh_token": refresh_token_value}).encode("utf-8")
        try:
            await http_client.proxy_request(request)
        except Exception as e:
            logger.warning(f"Logout request to auth-service failed, cookies will still be cleared: {e}")

    response = JSONResponse(content={"message": "Successfully logged out"})
    clear_auth_cookies(response)
    return response


@router.post("/validate")
async def validate_token(
    request: Request,
):
    """
    Валидация токена.

    Для обратной совместимости принимает token в body. Если token не передан,
    проверяет access token из HttpOnly cookie через auth-service.
    """
    body = {}
    try:
        body_bytes = await request.body()
        if body_bytes:
            body = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        body = {}

    token: Optional[str] = body.get("token") or request.cookies.get(settings.cookies.access_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token required",
        )

    request._body = json.dumps({"token": token}).encode("utf-8")
    service_response = await http_client.proxy_request(request)
    return Response(
        content=service_response.content,
        status_code=service_response.status_code,
        media_type=service_response.headers.get("content-type", "application/json"),
    )


# ========== ВЕРИФИКАЦИЯ EMAIL ==========

@router.post("/verify/request")
async def request_verification_code(
    request: Request,
):
    """Запросить код верификации на email."""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@router.post("/verify/confirm")
async def verify_email_code(
    confirm_data: VerifyConfirmRequest,
    request: Request,
):
    """Подтвердить email по коду."""
    request._body = json.dumps({"code": confirm_data.code}).encode("utf-8")
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    request_obj: Request,
):
    """Запросить сброс пароля — отправить код на email."""
    request_obj._body = json.dumps({"email": request.email}).encode("utf-8")
    response = await http_client.proxy_request(request_obj)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    request_obj: Request,
):
    """Подтвердить сброс пароля — проверить код и установить новый пароль."""
    request_obj._body = json.dumps(
        {
            "email": request.email,
            "code": request.code,
            "new_password": request.new_password,
        }
    ).encode("utf-8")
    response = await http_client.proxy_request(request_obj)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@router.get("/session")
async def get_current_session(request: Request):
    """
    Проверка текущей cookie-сессии.
    Endpoint защищён AuthMiddleware: если access cookie валидна, вернёт данные пользователя.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return {
        "authenticated": True,
        "user": user,
    }
