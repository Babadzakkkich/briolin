from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, Any, List, Optional

from app.services.profile_service import ProfileService
from app.dependencies import get_profile_service
from app.core.logger import logger
from app.core.exceptions import ProfileNotFoundException
from app.schemas.internal import SearchByEmbeddingRequest, SearchByEmbeddingResponse

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.get("/profiles/count")
async def get_profiles_count(
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения количества профилей
    """
    try:
        total = await service.get_profiles_count()
        return {"total": total}
    except Exception as e:
        logger.error(f"Failed to get profiles count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profiles/batch")
async def get_profiles_batch(
    request: Dict[str, List[str]] = Body(..., example={"keycloak_ids": ["uuid-1", "uuid-2"]}),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения нескольких профилей по Keycloak ID
    """
    try:
        keycloak_ids = request.get("keycloak_ids", [])
        if not keycloak_ids:
            return {"profiles": []}
        
        profiles = await service.get_profiles_batch_by_keycloak_ids(keycloak_ids)
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Failed to get profiles batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/exist")
async def check_profiles_exist(
    request: Dict[str, List[int]] = Body(..., example={"profile_ids": [1, 2, 3]}),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для проверки существования профилей
    """
    try:
        profile_ids = request.get("profile_ids", [])
        exist_map = await service.check_profiles_exist(profile_ids)
        return {"exist_map": exist_map}
    except Exception as e:
        logger.error(f"Failed to check profiles exist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/search")
async def search_profiles(
    request: Dict[str, Any] = Body(...),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для поиска профилей с фильтрацией
    Используется search-service
    """
    try:
        result = await service.search_profiles(
            gender=request.get("gender"),
            min_age=request.get("min_age"),
            max_age=request.get("max_age"),
            city=request.get("city"),
            education=request.get("education"),
            hobbies_keywords=request.get("hobbies_keywords"),
            partner_preferences=request.get("partner_preferences"),
            online_only=request.get("online_only", False),
            exclude_user_id=request.get("exclude_user_id"),
            exclude_keycloak_id=request.get("exclude_keycloak_id"),
            page=request.get("page", 1),
            limit=request.get("limit", 10)
        )
        return result
    except Exception as e:
        logger.error(f"Failed to search profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{keycloak_id}")
async def get_internal_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения профиля по Keycloak ID
    """
    try:
        profile = await service.get_full_profile_by_keycloak_id(keycloak_id)
        return profile
    except Exception as e:
        logger.error(f"Failed to get internal profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")


@router.get("/profiles/{keycloak_id}/basic")
async def get_internal_basic_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для получения базового профиля (легковесный)
    """
    try:
        profile = await service._get_basic_profile_by_keycloak_id(keycloak_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "id": profile.id,
            "keycloak_id": profile.keycloak_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "gender": profile.gender.value if hasattr(profile.gender, 'value') else profile.gender,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "city": profile.city,
            "online": profile.online,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get internal basic profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{keycloak_id}")
async def delete_internal_profile(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Внутренний эндпоинт для удаления профиля (используется auth-service)
    """
    try:
        success = await service.delete_profiles_by_keycloak_id(keycloak_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete internal profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles/{keycloak_id}/embedding")
async def get_profile_embedding(
    keycloak_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Get embedding vector for a user profile.
    Used by matching-service for semantic search.
    """
    try:
        embedding = await service.get_embedding(keycloak_id)
        if embedding is None:
            return {"embedding": []}
        return {"embedding": embedding}
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profiles/search_by_embedding", response_model=SearchByEmbeddingResponse)
async def search_profiles_by_embedding(
    request: SearchByEmbeddingRequest,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Search profiles by embedding similarity.
    Used by matching-service for targeted (premium) recommendations.
    
    Returns profiles sorted by cosine similarity (closest first),
    with similarity scores (0-1) where 1 = most similar.
    """
    try:
        profiles = await service.search_profiles_by_embedding(
            embedding=request.embedding,
            filters=request.filters,
            exclude_ids=request.exclude_ids,
            limit=request.limit,
            offset=request.offset
        )
        return SearchByEmbeddingResponse(profiles=profiles)
    except Exception as e:
        logger.error(f"Failed to search by embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/update_embedding")
async def update_profile_embedding(
    keycloak_id: str = Body(..., embed=True),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Manually trigger embedding update for a profile.
    Useful for backfilling existing profiles.
    """
    try:
        from app.services.embedding_updater import get_embedding_updater
        updater = get_embedding_updater()
        
        # Get basic profile
        basic = await service._get_basic_profile_by_keycloak_id(keycloak_id)
        if not basic:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        success = await updater.update_embedding_for_profile(basic.id)
        if success:
            return {"message": f"Embedding updated for user {keycloak_id}"}
        else:
            return {"message": f"No embedding generated for user {keycloak_id} (no detailed profile?)"}
    except Exception as e:
        logger.error(f"Failed to update embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))