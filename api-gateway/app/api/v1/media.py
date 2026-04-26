from fastapi import APIRouter, Request, Depends, Response, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from app.services.http_client import http_client
from app.schemas.media import (
    AvatarUploadResponse,
    AvatarDeleteResponse,
    AvatarResponse,
    ErrorResponse
)

router = APIRouter(prefix="/media", tags=["Media"])
security = HTTPBearer(auto_error=False)


@router.post(
    "/avatar",
    status_code=status.HTTP_201_CREATED,
    response_model=AvatarUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or max avatars exceeded"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        422: {"model": ErrorResponse, "description": "Image processing failed"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    },
    summary="Upload avatar",
    description="""
    Загрузка аватарки пользователя.
    
    - Поддерживаемые форматы: JPEG, PNG, WebP, GIF
    - Максимальный размер: 5MB
    - Изображение автоматически конвертируется в WebP
    - Создается thumbnail (200x200)
    - Максимум 10 аватарок на пользователя
    """
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
    "/avatars",
    response_model=List[AvatarResponse],
    summary="Get all user avatars",
    description="Получить все аватарки текущего пользователя"
)
async def get_my_avatars(
    request: Request,
    include_deleted: bool = Query(False, description="Включить удаленные аватарки"),
    limit: int = Query(20, ge=1, le=50, description="Количество на странице"),
    offset: int = Query(0, ge=0, description="Смещение"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить все аватарки текущего пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/my-avatar",
    responses={
        200: {"description": "Current avatar image"},
        404: {"model": ErrorResponse, "description": "No current avatar found"}
    },
    summary="Get my current avatar",
    description="Получить свою текущую аватарку (не нужно указывать ID). Автоматически находит is_current=True."
)
async def get_my_avatar(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получение своей текущей аватарки.
    Не требует указания keycloak_id или avatar_id.
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/my-thumbnail",
    responses={
        200: {"description": "Current thumbnail image"},
        404: {"model": ErrorResponse, "description": "No current thumbnail found"}
    },
    summary="Get my current thumbnail",
    description="Получить свой текущий thumbnail (не нужно указывать ID). Автоматически находит is_current=True."
)
async def get_my_thumbnail(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получение своего текущего thumbnail.
    Не требует указания keycloak_id или avatar_id.
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put(
    "/avatar/{avatar_id}/set-current",
    status_code=status.HTTP_200_OK,
    summary="Set current avatar",
    description="Установить аватарку как текущую"
)
async def set_current_avatar(
    avatar_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Установить аватарку как текущую"""
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
        404: {"model": ErrorResponse, "description": "Avatar not found"}
    },
    summary="Get avatar"
)
async def get_avatar(
    keycloak_id: str,
    avatar_id: str = Query(..., description="ID аватарки"),
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
        404: {"model": ErrorResponse, "description": "Thumbnail not found"}
    },
    summary="Get avatar thumbnail"
)
async def get_avatar_thumbnail(
    keycloak_id: str,
    avatar_id: str = Query(..., description="ID аватарки"),
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
    "/my-avatar",
    status_code=status.HTTP_200_OK,
    response_model=AvatarDeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "No current avatar found"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    },
    summary="Delete my current avatar",
    description="""
    Удаление своей текущей аватарки (soft delete).
    
    - Автоматически находит аватарку с is_current=True
    - Не нужно указывать avatar_id
    - Следующая по дате загрузки становится текущей
    """
)
async def delete_my_avatar(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Удаление своей текущей аватарки.
    Не требует указания avatar_id.
    """
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Avatar not found"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    },
    summary="Delete avatar",
    description="""
    Удаление аватарки пользователя (soft delete).
    
    - Если удаляется текущая аватарка, следующая по дате загрузки становится текущей
    - Аватарка помечается как удаленная, но файлы остаются в MinIO
    - Для полного удаления нужны права администратора
    """
)
async def delete_avatar(
    avatar_id: str = Query(..., description="ID аватарки"),
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


@router.delete(
    "/avatar/{avatar_id}/permanent",
    status_code=status.HTTP_200_OK,
    summary="Permanently delete avatar",
    description="Полное удаление аватарки (только для администраторов)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Avatar not found"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    }
)
async def delete_avatar_permanent(
    avatar_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Полное удаление аватарки (только администраторы)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )