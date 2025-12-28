from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.core.logger import logger
from app.core.exceptions import DatabaseException

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.get("/users/{keycloak_id}", status_code=status.HTTP_200_OK)
async def get_user_basic_info(
    keycloak_id: str,
    service: AuthService = Depends(get_auth_service)
):
    """
    Внутренний эндпоинт для получения базовой информации о пользователе
    """
    user_info = await service.get_user_basic_info(keycloak_id)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_info

@router.get("/users/{keycloak_id}/active", status_code=status.HTTP_200_OK)
async def check_user_active(
    keycloak_id: str,
    service: AuthService = Depends(get_auth_service)
):
    """Внутренняя проверка активности пользователя"""
    is_active = await service.check_user_active(keycloak_id)
    return {"keycloak_id": keycloak_id, "is_active": is_active}

@router.get("/users/{keycloak_id}/exists", status_code=status.HTTP_200_OK)
async def check_user_exists(
    keycloak_id: str,
    service: AuthService = Depends(get_auth_service)
):
    """Внутренняя проверка существования пользователя"""
    exists = await service.check_user_exists(keycloak_id)
    return {"exists": exists}

@router.patch("/users/{keycloak_id}", status_code=status.HTTP_200_OK)
async def update_user_in_auth(
    keycloak_id: str,
    update_data: dict,
    service: AuthService = Depends(get_auth_service)
):
    """
    Внутренний эндпоинт для обновления пользователя в auth-db
    """
    try:
        success = await service.update_user_in_auth_db(keycloak_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="User not found in auth-db")
        return {"message": "User updated successfully in auth-db"}
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{keycloak_id}", status_code=status.HTTP_200_OK)
async def delete_user_from_auth(
    keycloak_id: str,
    service: AuthService = Depends(get_auth_service)
):
    """
    Внутренний эндпоинт для удаления пользователя из auth-db
    """
    try:
        success = await service.delete_user_from_auth_db(keycloak_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found in auth-db")
        return {"message": "User deleted successfully from auth-db"}
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))