from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.services.profile_service import ProfileService
from app.schemas.profile import (
    BasicProfileCreate, DetailedProfileCreate, FullProfileCreate, FullProfileUpdate,
    FullProfileResponse
)
from app.dependencies import get_profile_service, get_current_user
from app.core.logger import logger
from app.core.exceptions import ProfileNotFoundException

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("/saga/{saga_id}/status")
async def get_saga_status(
    saga_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """Получение статуса операции по ID саги"""
    status = await service.get_saga_status(saga_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Saga not found")
    return status

@router.post("/basic", status_code=status.HTTP_202_ACCEPTED)
async def create_basic_profile(
    profile_data: BasicProfileCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ создание только базового профиля"""
    try:
        result = await service.create_basic_profile(
            keycloak_id=current_user["keycloak_id"],
            basic_data=profile_data,
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create basic profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detailed", status_code=status.HTTP_202_ACCEPTED)
async def create_detailed_profile(
    profile_data: DetailedProfileCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ создание только детального профиля"""
    try:
        result = await service.create_detailed_profile(
            keycloak_id=current_user["keycloak_id"],
            detailed_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Basic profile not found. Create basic profile first.")
    except Exception as e:
        logger.error(f"Failed to create detailed profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение своего полного профиля"""
    try:
        profile = await service.get_full_profile_by_keycloak_id(current_user["keycloak_id"])
        return profile
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/me", status_code=status.HTTP_202_ACCEPTED)
async def update_my_profile(
    profile_data: FullProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ обновление своего полного профиля"""
    try:
        result = await service.update_full_profile(
            keycloak_id=current_user["keycloak_id"],
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ удаление своего полного профиля"""
    try:
        result = await service.delete_full_profile(
            keycloak_id=current_user["keycloak_id"],
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{keycloak_id}", response_model=FullProfileResponse)
async def get_profile_by_id(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        profile = await service.get_full_profile_by_keycloak_id(keycloak_id)
        return profile
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_profile_by_id(
    keycloak_id: str,
    profile_data: FullProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ обновление профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        result = await service.update_full_profile(
            keycloak_id=keycloak_id,
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_profile_by_id(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ удаление профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        result = await service.delete_full_profile(
            keycloak_id=keycloak_id,
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))