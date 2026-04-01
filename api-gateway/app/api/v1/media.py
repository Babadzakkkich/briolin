from fastapi import APIRouter, Request, Depends, Response, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.http_client import http_client
from app.schemas.media import (
    AvatarUploadResponse,
    AvatarDeleteResponse,
    ErrorResponse
)

router = APIRouter(prefix="/media", tags=["Media"])
security = HTTPBearer(auto_error=False)


@router.post(
    "/avatar",
    status_code=status.HTTP_201_CREATED,
    response_model=AvatarUploadResponse,
    responses={
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Загрузка аватарки.
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/avatar/{keycloak_id}",
    responses={
        200: {"description": "Avatar image"},
        404: {"model": ErrorResponse}
    }
)
async def get_avatar(
    keycloak_id: str,
    avatar_id: Optional[str] = Query(None),
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение аватарки"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/avatar/{keycloak_id}/thumbnail",
    responses={
        200: {"description": "Avatar thumbnail"},
        404: {"model": ErrorResponse}
    }
)
async def get_avatar_thumbnail(
    keycloak_id: str,
    avatar_id: Optional[str] = Query(None),
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение thumbnail аватарки"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.delete(
    "/avatar",
    status_code=status.HTTP_200_OK,
    response_model=AvatarDeleteResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def delete_avatar(
    avatar_id: str = Query(...),
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление аватарки"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )