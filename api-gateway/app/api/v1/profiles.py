from fastapi import APIRouter, Request, Depends, Response, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.http_client import http_client
from app.schemas.profile import (
    FullProfileCreate,
    FullProfileUpdate,
    FullProfileResponse,
    BasicProfileResponse,
    ProfileListResponse
)
from app.schemas.auth import UserRole

router = APIRouter(prefix="/profiles", tags=["Profiles"])
security = HTTPBearer(auto_error=False)

@router.post("/", response_model=FullProfileResponse)
async def create_profile(
    profile_data: FullProfileCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Создание полного профиля (basic + detailed)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put("/me", response_model=FullProfileResponse)
async def update_my_profile(
    profile_data: FullProfileUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

# @router.get("/online")
# async def get_online_users(
#     request: Request,
#     skip: int = Query(0, ge=0, description="Skip records"),
#     limit: int = Query(50, ge=1, le=100, description="Limit records"),
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     """
#     Получение списка онлайн пользователей с пагинацией.
#     Проксирует запрос в profile-service (/api/v1/profiles/online).
#     """
#     async def receive():
#         return {"type": "http.request", "body": b""}
    
#     # Копируем scope и обновляем path
#     scope = dict(request.scope)
#     scope["path"] = "/api/v1/profiles/online"
#     scope["raw_path"] = b"/api/v1/profiles/online"
#     scope["query_string"] = request.scope["query_string"]
    
#     new_request = Request(scope, receive)
    
#     response = await http_client.proxy_request(new_request)
#     return Response(
#         content=response.content,
#         status_code=response.status_code,
#         headers=dict(response.headers)
#     )

# @router.get("/online/{keycloak_id}")
# async def get_user_online_status(
#     keycloak_id: str,
#     request: Request,
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     """
#     Проверка онлайн статуса конкретного пользователя.
#     Проксирует запрос в profile-service (/api/v1/profiles/{keycloak_id}/online).
#     """
#     async def receive():
#         return {"type": "http.request", "body": b""}
    
#     # Копируем scope и обновляем path
#     scope = dict(request.scope)
#     scope["path"] = f"/api/v1/profiles/{keycloak_id}/online"
#     scope["raw_path"] = f"/api/v1/profiles/{keycloak_id}/online".encode()
#     scope["query_string"] = request.scope["query_string"]
    
#     new_request = Request(scope, receive)
    
#     response = await http_client.proxy_request(new_request)
#     return Response(
#         content=response.content,
#         status_code=response.status_code,
#         headers=dict(response.headers)
#     )

@router.get("/{keycloak_id}", response_model=FullProfileResponse)
async def get_profile_by_id(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put("/{keycloak_id}", response_model=FullProfileResponse)
async def update_profile_by_id(
    keycloak_id: str,
    profile_data: FullProfileUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/{keycloak_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_by_id(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )