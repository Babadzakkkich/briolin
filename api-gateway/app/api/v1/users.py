from fastapi import APIRouter, Request, Depends, Response, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.http_client import http_client
from app.dependencies import get_current_user, require_role
from app.schemas.user import UserPublic, UserList, UserBase, UserRolesUpdate, UserMeResponse
from app.schemas.auth import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

# Схема безопасности для роутов, требующих авторизации
security = HTTPBearer(auto_error=False)

@router.get("/", response_model=UserList)
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    is_active: bool = Query(None, description="Filter by active status"),
    search: str = Query(None, description="Search in username, email, first/last name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить список пользователей с пагинацией и фильтрацией
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/me", response_model=UserMeResponse)
async def get_my_info(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получение информации о текущем пользователе
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить пользователя по ID
    
    Можно получить информацию о себе или если есть роль admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить пользователя по username
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/email/{email}", response_model=UserPublic)
async def get_user_by_email(
    email: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить пользователя по email
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_data: UserBase,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Обновить данные пользователя
    
    Можно обновить свой профиль или если есть роль admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put("/{user_id}/roles", response_model=UserPublic)
async def update_user_roles(
    user_id: int,
    roles_data: UserRolesUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Обновить роли пользователя
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Удалить пользователя
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.patch("/{user_id}/toggle-status", response_model=UserPublic)
async def toggle_user_status(
    user_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Переключить статус активности пользователя
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/{user_id}/exists")
async def check_user_exists(
    user_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Проверить существование пользователя
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/role/{role}", response_model=UserList)
async def get_users_by_role(
    role: UserRole,
    request: Request,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить пользователей по роли
    
    Требуется роль: admin
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )