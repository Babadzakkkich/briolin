from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.core.exceptions import ValidationException, DatabaseException

router = APIRouter(prefix="/auth/verify", tags=["Email Verification"])


class VerifyCodeRequest(BaseModel):
    code: str


@router.post("/request", status_code=status.HTTP_200_OK)
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


@router.post("/confirm", status_code=status.HTTP_200_OK)
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