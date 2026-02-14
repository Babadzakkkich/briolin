from typing import Optional
from fastapi import APIRouter, Request, Depends, Response, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.http_client import http_client

router = APIRouter(prefix="/online", tags=["Online Status"])
security = HTTPBearer(auto_error=False)


@router.get("/users")
async def get_online_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получение списка онлайн пользователей.
    Проксирует запрос в profile-service (/api/v1/profiles/online).
    """
    # Меняем путь для profile-service
    response = await http_client.proxy_request(
        request, 
        path_override="/api/v1/profiles/online"
    )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get("/users/{keycloak_id}")
async def get_user_online_status(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Проверка онлайн статуса конкретного пользователя.
    Проксирует запрос в profile-service.
    """
    response = await http_client.proxy_request(
        request,
        path_override=f"/api/v1/profiles/{keycloak_id}/online"
    )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )