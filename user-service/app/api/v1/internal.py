from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.services.user_service import UserService
from app.schemas.internal import UserProfileCreate, UserProfileResponse
from app.dependencies import get_user_service
from app.core.logger import logger

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserProfileResponse)
async def create_user_profile(
    data: UserProfileCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Внутренний эндпоинт для создания профиля пользователя из auth-service
    """
    try:
        user = await service.create_user_profile(data)
        return UserProfileResponse(
            keycloak_id=user.keycloak_id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except Exception as e:
        logger.error(f"Failed to create user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create user profile")

@router.get("/users/{keycloak_id}", response_model=UserProfileResponse)
async def get_user_by_keycloak_id(
    keycloak_id: str,
    service: UserService = Depends(get_user_service)
):
    """
    Внутренний эндпоинт для получения пользователя по Keycloak ID
    """
    user = await service.get_user_by_keycloak_id(keycloak_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        keycloak_id=user.keycloak_id,
        username=user.username,
        email=user.email,
        roles=user.roles,
        is_active=user.is_active,
        created_at=user.created_at
    )