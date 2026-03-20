from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 дней

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
    return await service.register(await request.json())

@router.post("/login")
async def login_user(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """Аутентификация пользователя (публичный эндпоинт)"""
    token_data = await service.login(await request.json())
    refresh_token = token_data.get("refresh_token")

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=token_data.get("refresh_expires_in", REFRESH_COOKIE_MAX_AGE),
    )

    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
    }

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """Обновление токена (публичный эндпоинт)"""
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    token_data = await service.refresh_token({"refresh_token": refresh_token})

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token_data.get("refresh_token"),
        httponly=True,
        samesite="lax",
        max_age=token_data.get("refresh_expires_in", REFRESH_COOKIE_MAX_AGE),
    )

    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
    }

@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """Выход из системы"""
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active session")

    await service.logout(refresh_token)
    response.delete_cookie(REFRESH_COOKIE)
    return {"message": "Successfully logged out"}

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