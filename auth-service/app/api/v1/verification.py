from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.core.exceptions import ValidationException, DatabaseException
from app.schemas.verify import VerifyCodeRequest, PasswordResetRequest, PasswordResetConfirmRequest

router = APIRouter(prefix="/auth")


@router.post("/verify/request", status_code=status.HTTP_200_OK)
async def request_verification_code(
    service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Запросить код верификации на email.
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")
        
        result = await service.request_verification_code(user_email)
        return result
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/confirm", status_code=status.HTTP_200_OK)
async def verify_email_code(
    request: VerifyCodeRequest,
    service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Подтвердить email по коду.
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")
        
        result = await service.verify_email_code(user_email, request.code)
        return result
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service)
):
    """
    Запросить сброс пароля — отправить код на email.
    Публичный эндпоинт.
    """
    try:
        result = await service.request_password_reset(request.email)
        return result
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    service: AuthService = Depends(get_auth_service)
):
    """
    Подтвердить сброс пароля — проверить код и установить новый пароль.
    Публичный эндпоинт.
    """
    try:
        result = await service.confirm_password_reset(
            request.email, request.code, request.new_password
        )
        return result
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))