from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.services.minio_client import get_minio_client, MinIOClient
from app.core.logger import logger
from app.schemas.media import AvatarResponse

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get(
    "/avatars/{keycloak_id}",
    response_model=Optional[AvatarResponse],
    summary="Get avatar info (internal)",
    description="Внутренний эндпоинт для получения информации об аватарке"
)
async def get_avatar_info_internal(
    keycloak_id: str,
    avatar_id: Optional[str] = None,
    minio_client: MinIOClient = Depends(get_minio_client)
):
    """Получение информации об аватарке (для других сервисов)"""
    try:
        if avatar_id:
            object_name = f"avatars/{keycloak_id}/{avatar_id}/original.webp"
        else:
            # Можно добавить получение последней аватарки из БД
            raise HTTPException(status_code=404, detail="Avatar not found")
        
        # Проверяем существование
        try:
            await minio_client.get_file(object_name)
        except:
            return None
        
        # Формируем URL
        public_url = f"/media/avatar/{keycloak_id}?avatar_id={avatar_id}"
        thumbnail_url = f"/media/avatar/{keycloak_id}/thumbnail?avatar_id={avatar_id}"
        
        return AvatarResponse(
            avatar_id=avatar_id,
            url=public_url,
            thumbnail_url=thumbnail_url,
            width=0,  # Можно добавить метаданные в БД
            height=0,
            file_size=0,
            created_at=None
        )
        
    except Exception as e:
        logger.error(f"Failed to get avatar info: {e}")
        return None