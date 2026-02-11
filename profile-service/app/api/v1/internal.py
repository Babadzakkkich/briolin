from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.services.profile_service import ProfileService
from app.dependencies import get_profile_service
from app.core.logger import logger
from app.schemas.internal import ProfileDeleteData

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.get("/profiles/{keycloak_id}")
async def get_internal_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения профиля по Keycloak ID
    """
    try:
        profile = await service.get_full_profile_by_keycloak_id(keycloak_id)  # Исправлено: публичный метод
        return profile
    except Exception as e:
        logger.error(f"Failed to get internal profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/profiles/{keycloak_id}/basic")
async def get_internal_basic_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения базового профиля (легковесный)
    """
    try:
        profile = await service._get_basic_profile_by_keycloak_id(keycloak_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "id": profile.id,
            "keycloak_id": profile.keycloak_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "gender": profile.gender,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "city": profile.city,
            "online": profile.online,
            "avatar_url": None,  # Добавьте поле в модель если нужно
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
        }
    except Exception as e:
        logger.error(f"Failed to get internal basic profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")

@router.delete("/profiles/{keycloak_id}")
async def delete_internal_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для удаления профиля (используется auth-service)
    """
    try:
        success = await service.delete_profiles_by_keycloak_id(keycloak_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete internal profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))