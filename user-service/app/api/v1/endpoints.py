from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from uuid import UUID

from app.services.user_service import UserService
from app.schemas.user import UserPublic, UserList, UserUpdate, UserInfo
from app.dependencies import get_user_service, get_current_user, require_role
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    is_active: bool = Query(None, description="Filter by active status"),
    search: str = Query(None, description="Search in username, email, first/last name"),
    current_user: dict = Depends(require_role("admin")),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Получить список пользователей с пагинацией и фильтрацией
    Требуется роль admin
    """
    users, total = await service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active,
        search=search
    )
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователя по ID
    Можно получить информацию о себе или если есть роль admin
    """
    # Проверяем права: либо свой профиль, либо админ
    if str(user_id) != current_user["id"] and "admin" not in current_user["roles"]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    try:
        return await service.get_user_by_id(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    current_user: dict = Depends(require_role("admin")),  # Только для админов
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
    current_user: dict = Depends(require_role("admin")),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя по email (только для админов)"""
    user = await service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Обновить данные пользователя
    Можно обновить свой профиль или если есть роль admin
    """
    # Проверяем права: либо свой профиль, либо админ
    if str(user_id) != current_user["id"] and "admin" not in current_user["roles"]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    try:
        return await service.update_user(user_id, user_data)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(require_role("admin")),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Удалить пользователя (deactivate)
    Требуется роль admin
    """
    try:
        await service.delete_user(user_id)
        return {"message": "User deactivated successfully"}
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{user_id}/toggle-status", response_model=UserPublic)
async def toggle_user_status(
    user_id: UUID,
    current_user: dict = Depends(require_role("admin")),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Переключить статус активности пользователя
    Требуется роль admin
    """
    try:
        return await service.toggle_user_status(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{user_id}/exists")
async def check_user_exists(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Проверить существование пользователя
    """
    try:
        await service.get_user_by_id(user_id)
        return {"exists": True}
    except UserNotFoundException:
        return {"exists": False}
    except Exception:
        return {"exists": False}

# Добавляем новый endpoint для внутренних вызовов
@router.post("/sync", response_model=UserPublic, status_code=201)
async def sync_user(
    user_info: UserInfo,
    # Проверяем, что вызов внутренний (от Gateway)
    x_internal_call: Optional[str] = Header(None, alias="X-Internal-Call"),
    service: UserService = Depends(get_user_service)
):
    """
    Синхронизация пользователя из Keycloak в локальную БД
    Используется для компенсационных транзакций
    Только для внутренних вызовов от Gateway
    """
    # Проверяем, что вызов внутренний
    if not x_internal_call or x_internal_call != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for internal use only"
        )
    
    try:
        return await service.create_user(
            keycloak_id=user_info.keycloak_id,
            email=user_info.email,
            username=user_info.username,
            first_name=user_info.first_name,
            last_name=user_info.last_name
        )
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))