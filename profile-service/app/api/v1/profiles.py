from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.services.profile_service import ProfileService
from app.schemas.profile import (
    FullProfileCreate, FullProfileUpdate,
    FullProfileResponse, BasicProfileResponse
)
from app.dependencies import get_profile_service, get_current_user, require_test_passed
from app.core.logger import logger

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: FullProfileCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Создание полного профиля (basic + detailed)"""
    try:
        result = await service.create_full_profile(
            keycloak_id=current_user["keycloak_id"],
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update_profile(
    profile_data: FullProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Обновление полного профиля"""
    try:
        result = await service.update_full_profile(
            keycloak_id=current_user["keycloak_id"],
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Удаление полного профиля"""
    try:
        success = await service.delete_full_profile(
            keycloak_id=current_user["keycloak_id"],
            current_user=current_user
        )
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение своего полного профиля"""
    try:
        profile = await service._get_full_profile_by_keycloak_id(current_user["keycloak_id"])
        return profile
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/{keycloak_id}")
async def get_profile_by_id(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        profile = await service._get_full_profile_by_keycloak_id(keycloak_id)
        return profile
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")

@router.patch("/online/{status}")
async def update_online_status(
    status: bool,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Обновление онлайн статуса"""
    try:
        success = await service.update_online_status(current_user["keycloak_id"], status)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Online status updated"}
    except Exception as e:
        logger.error(f"Failed to update online status: {e}")
        raise HTTPException(status_code=500, detail=str(e))