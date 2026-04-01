from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.core.exceptions import UserAlreadyExistsException, ValidationException
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
):
    """
    СИНХРОННАЯ регистрация нового пользователя.
    Возвращает созданного пользователя с кодом 201.
    """
    try:
        result = await service.register(user_data.model_dump())
        return result
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
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
    """Валидация токена"""
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token required"
        )
    
    response = await service.validate_token(token)
    return response