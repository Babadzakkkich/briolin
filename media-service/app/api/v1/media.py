from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import Optional

from app.services.media_service import get_media_service, MediaService
from app.dependencies import get_current_user, validate_file
from app.core.logger import logger
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedMediaTypeException,
    ImageProcessingException,
    FileNotFoundException
)
from app.schemas.media import (
    AvatarUploadResponse,
    AvatarDeleteResponse,
    ErrorResponse
)

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/avatar",
    status_code=status.HTTP_201_CREATED,
    response_model=AvatarUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        422: {"model": ErrorResponse, "description": "Image processing failed"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    },
    summary="Upload avatar"
)
async def upload_avatar(
    file: UploadFile = File(..., description="Файл аватарки"),
    current_user: dict = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Загрузка аватарки пользователя
    
    - Поддерживаемые форматы: JPEG, PNG, WebP, GIF
    - Максимальный размер: 5MB
    - Изображение автоматически конвертируется в WebP
    - Создается thumbnail (200x200)
    """
    try:
        # Валидация файла
        file_data, content_type = await validate_file(file)
        
        # Загрузка аватарки через сервис
        result = await media_service.upload_avatar(
            file_data=file_data,
            filename=file.filename,
            content_type=content_type,
            keycloak_id=current_user["keycloak_id"]
        )
        
        return result
        
    except FileTooLargeException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except UnsupportedMediaTypeException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ImageProcessingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")


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
    avatar_id: str,
    media_service: MediaService = Depends(get_media_service)
):
    """
    Получение аватарки пользователя по ID
    """
    try:
        file_data, content_type = await media_service.get_avatar(
            keycloak_id=keycloak_id,
            avatar_id=avatar_id
        )
        
        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400"
            }
        )
        
    except FileNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to get avatar: {e}")
        raise HTTPException(status_code=404, detail="Avatar not found")


@router.get(
    "/avatar/{keycloak_id}/thumbnail",
    responses={
        200: {"description": "Thumbnail image"},
        404: {"model": ErrorResponse, "description": "Thumbnail not found"}
    },
    summary="Get avatar thumbnail"
)
async def get_avatar_thumbnail(
    keycloak_id: str,
    avatar_id: str,
    media_service: MediaService = Depends(get_media_service)
):
    """
    Получение thumbnail аватарки пользователя
    """
    try:
        file_data, content_type = await media_service.get_avatar_thumbnail(
            keycloak_id=keycloak_id,
            avatar_id=avatar_id
        )
        
        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400"
            }
        )
        
    except FileNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to get thumbnail: {e}")
        raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.delete(
    "/avatar",
    status_code=status.HTTP_200_OK,
    response_model=AvatarDeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Avatar not found"},
        503: {"model": ErrorResponse, "description": "MinIO unavailable"}
    },
    summary="Delete avatar"
)
async def delete_avatar(
    avatar_id: str,
    current_user: dict = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Удаление аватарки пользователя
    
    - Если удаляется текущая аватарка, профиль пользователя будет обновлен
    - Если удаляется старая аватарка, просто удаляются файлы
    """
    try:
        result = await media_service.delete_avatar(
            keycloak_id=current_user["keycloak_id"],
            avatar_id=avatar_id
        )
        
        return result
        
    except FileNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to delete avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete avatar")