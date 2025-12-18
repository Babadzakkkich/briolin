from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.services.user_service import UserService
from app.schemas.user import UserPublic, UserList, UserBase, UserRolesUpdate, UserMeResponse
from app.dependencies import get_user_service, get_current_user, get_current_active_user, require_role
from app.database.models import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    is_active: bool = Query(None, description="Filter by active status"),
    search: str = Query(None, description="Search in username, email, first/last name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
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
        search=search,
        role=role
    )
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/keycloak/{keycloak_id}", response_model=UserPublic)
async def get_user_by_keycloak_id(
    keycloak_id: str,
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователя по Keycloak ID
    Используется API Gateway для кэширования
    """
    user = await service.get_user_by_keycloak_id(keycloak_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user


@router.get("/me", response_model=UserMeResponse)
async def get_my_info(
    current_user: dict = Depends(get_current_active_user),  # Проверяем, что пользователь активен
    service: UserService = Depends(get_user_service)
):
    """
    Получение информации о текущем пользователе
    """
    return await service.get_my_info(current_user["id"])

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователя по ID
    Можно получить информацию о себе или если есть роль admin
    """
    # Проверяем права: либо свой профиль, либо админ
    if user_id != current_user["id"] and UserRole.ADMIN not in current_user["roles"]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    return await service.get_user_by_id(user_id)

@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя по username (только для админов)"""
    user = await service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.get("/email/{email}", response_model=UserPublic)
async def get_user_by_email(
    email: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя по email (только для админов)"""
    user = await service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_data: UserBase,
    current_user: dict = Depends(get_current_active_user),  # Проверяем, что пользователь активен
    service: UserService = Depends(get_user_service)
):
    """
    Обновить данные пользователя (только базовые поля)
    Можно обновить свой профиль или если есть роль admin
    """
    # Проверяем права: либо свой профиль, либо админ
    is_self = user_id == current_user["id"]
    is_admin = UserRole.ADMIN in current_user["roles"]
    
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    return await service.update_user(user_id, user_data)

@router.put("/{user_id}/roles", response_model=UserPublic)
async def update_user_roles(
    user_id: int,
    roles_data: UserRolesUpdate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Обновить роли пользователя
    Требуется роль admin
    """
    return await service.update_user_roles(user_id, roles_data)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    ПОЛНОЕ УДАЛЕНИЕ пользователя из БД и Keycloak
    Требуется роль admin
    """
    await service.delete_user(user_id)
    return {"message": "User deleted successfully"}

@router.patch("/{user_id}/toggle-status", response_model=UserPublic)
async def toggle_user_status(
    user_id: int,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Переключить статус активности пользователя
    Требуется роль admin
    """
    return await service.toggle_user_status(user_id)

@router.get("/{user_id}/exists")
async def check_user_exists(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Проверить существование пользователя
    """
    try:
        await service.get_user_by_id(user_id)
        return {"exists": True}
    except HTTPException:
        return {"exists": False}

@router.get("/role/{role}", response_model=UserList)
async def get_users_by_role(
    role: UserRole,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),  # Только для админов
    service: UserService = Depends(get_user_service)
):
    """
    Получить пользователей по роли
    Требуется роль admin
    """
    users = await service.get_users_by_role(role)
    
    # Применяем пагинацию
    total = len(users)
    paginated_users = users[skip:skip + limit]
    
    return UserList(
        users=paginated_users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )