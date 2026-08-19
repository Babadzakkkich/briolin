from fastapi import APIRouter, Depends, HTTPException, status, Request
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
    credentials: UserLogin,
    service: AuthService = Depends(get_auth_service)
):
    """Аутентификация пользователя"""
    response = await service.login(credentials.model_dump())
    return response


@router.post("/refresh")
async def refresh_token(
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Обновление токена"""
    body = await request.json()
    response = await service.refresh_token(body)
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