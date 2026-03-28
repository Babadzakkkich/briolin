from fastapi import APIRouter, Request, Depends, Response, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.http_client import http_client
from app.schemas.user import (
    UserBase, 
    UserPublic, 
    UserList, 
    UserRolesUpdate, 
    UserMeResponse,
    SagaStatusResponse,
    AsyncOperationResponse
)
from shared.schemas.shared import UserRole

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer(auto_error=False)

@router.get("/saga/{saga_id}/status", response_model=SagaStatusResponse)
async def get_saga_status(
    saga_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение статуса операции по ID саги"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/", response_model=UserList)
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить список пользователей с пагинацией (только для админов)"""
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
    """Получение информации о текущем пользователе"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/{keycloak_id}", response_model=UserPublic)
async def get_user(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить пользователя по Keycloak ID"""
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
    """Получить пользователя по username (только для админов)"""
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
    """Получить пользователя по email (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put(
    "/{keycloak_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def update_user(
    keycloak_id: str,
    user_data: UserBase,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ обновление данных пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put(
    "/{keycloak_id}/roles", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def update_user_roles(
    keycloak_id: str,
    roles_data: UserRolesUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ обновление ролей пользователя (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete(
    "/{keycloak_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def delete_user(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ удаление пользователя (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.patch(
    "/{keycloak_id}/toggle-status", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def toggle_user_status(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ переключение статуса активности пользователя (только для админов)"""
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить пользователей по роли (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
    
@router.get("/{keycloak_id}/exists")
async def check_user_exists(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Проверить существование пользователя по Keycloak ID"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )