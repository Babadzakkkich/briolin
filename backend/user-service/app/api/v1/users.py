from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from app.services.user_service import UserService
from app.schemas.user import UserPublic, UserList, UserBase, UserRolesUpdate, UserMeResponse
from app.dependencies import get_user_service, get_current_user, get_current_active_user, require_role
from shared.schemas.shared import UserRole
from app.core.logger import logger

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/saga/{saga_id}/status")
async def get_saga_status(
    saga_id: str,
    service: UserService = Depends(get_user_service)
):
    """Получение статуса операции по ID саги"""
    status = await service.get_saga_status(saga_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Saga not found")
    return status

@router.get("/", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """
    Получить список пользователей с пагинацией
    Требуется роль admin
    """
    users, total = await service.list_users(
        skip=skip,
        limit=limit
    )
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/me", response_model=UserMeResponse)
async def get_my_info(
    current_user: dict = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Получение информации о текущем пользователе
    """
    return await service.get_my_info(current_user["keycloak_id"])

@router.get("/{keycloak_id}", response_model=UserPublic)
async def get_user(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователя по Keycloak ID
    Можно получить информацию о себе или если есть роль admin
    """
    if keycloak_id != current_user["keycloak_id"] and UserRole.ADMIN not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = await service.get_user_by_keycloak_id(keycloak_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя по username (только для админов)"""
    user = await service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/email/{email}", response_model=UserPublic)
async def get_user_by_email(
    email: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя по email (только для админов)"""
    user = await service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_user(
    keycloak_id: str,
    user_data: UserBase,
    current_user: dict = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Обновить данные пользователя (только базовые поля)
    Можно обновить свой профиль или если есть роль admin
    Возвращает 202 Accepted с ID саги для отслеживания
    """
    return await service.update_user(
        keycloak_id=keycloak_id,
        user_data=user_data,
        current_user=current_user
    )

@router.put("/{keycloak_id}/roles", status_code=status.HTTP_202_ACCEPTED)
async def update_user_roles(
    keycloak_id: str,
    roles_data: UserRolesUpdate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """
    Обновить роли пользователя
    Требуется роль admin
    Возвращает 202 Accepted с ID саги для отслеживания
    """
    return await service.update_user_roles(
        keycloak_id=keycloak_id,
        roles_data=roles_data,
        current_user=current_user
    )

@router.delete("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_user(
    keycloak_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """
    ПОЛНОЕ УДАЛЕНИЕ пользователя из БД и Keycloak
    Требуется роль admin
    Возвращает 202 Accepted с ID саги для отслеживания
    """
    return await service.delete_user(
        keycloak_id=keycloak_id,
        current_user=current_user
    )

@router.patch("/{keycloak_id}/toggle-status", status_code=status.HTTP_202_ACCEPTED)
async def toggle_user_status(
    keycloak_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """
    Переключить статус активности пользователя
    Требуется роль admin
    Возвращает 202 Accepted с ID саги для отслеживания
    """
    return await service.toggle_user_status(
        keycloak_id=keycloak_id,
        current_user=current_user
    )

@router.get("/role/{role}", response_model=UserList)
async def get_users_by_role(
    role: UserRole,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователей по роли
    Требуется роль admin
    """
    users, total = await service.get_users_by_role(role, skip=skip, limit=limit)
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )
    
@router.get("/{keycloak_id}/exists")
async def check_user_exists(
    keycloak_id: str,
    service: UserService = Depends(get_user_service)
):
    """
    Проверить существование пользователя по Keycloak ID
    """
    exists = await service.check_user_exists(keycloak_id)
    return {"exists": exists}