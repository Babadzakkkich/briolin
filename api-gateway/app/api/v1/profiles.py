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

@router.put("/", response_model=FullProfileResponse)
async def update_profile(
    profile_data: FullProfileUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление полного профиля"""
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

@router.patch("/online/{status}")
async def update_online_status(
    status: bool,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление онлайн статуса"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )