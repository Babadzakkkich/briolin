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
        profile = await service.get_full_profile_by_keycloak_id(keycloak_id)
        return profile
    except Exception as e:
        logger.error(f"Failed to get internal profile: {e}")
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