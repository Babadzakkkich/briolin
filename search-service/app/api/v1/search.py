from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.schemas.search import (
    SearchWithPaginationRequest,
    TargetedSearchWithPaginationRequest,
    SearchResponse,
    SearchSessionInfo,
    SearchLockInfo,
    ErrorResponse
)
from app.services.search import SearchService
from app.dependencies import get_search_service
from app.core.exceptions import SearchServiceException, SearchLockedException, SearchSessionNotFoundException
from app.core.logger import logger
from shared.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "/classic",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def classic_search(
        search_request: SearchWithPaginationRequest,
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Выполняет классический поиск по профилям
    """
    try:
        keycloak_id = current_user.get("keycloak_id")

        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        return await search_service.classic_search(
            keycloak_id=keycloak_id,
            search_params=search_request,
            page=search_request.page,
            limit=search_request.limit
        )
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in classic_search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/targeted",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def targeted_search(
        search_request: TargetedSearchWithPaginationRequest,
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Выполняет таргетированный поиск с использованием detailed_profiles
    """
    try:
        keycloak_id = current_user.get("keycloak_id")

        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        return await search_service.targeted_search(
            keycloak_id=keycloak_id,
            search_params=search_request,
            page=search_request.page,
            limit=search_request.limit
        )
    except SearchLockedException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "unlock_time": e.unlock_time.isoformat() if e.unlock_time else None,
                "time_until_unlock": e.time_until_unlock,
                "profiles_viewed": e.profiles_viewed
            }
        )
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in targeted_search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/lock-status",
    response_model=SearchLockInfo,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_lock_status(
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение статуса блокировки таргетированного поиска для текущего пользователя
    """
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        return await search_service.get_search_lock_status(keycloak_id)
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_search_lock_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/history",
    response_model=List[SearchSessionInfo],
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_history(
        limit: int = Query(50, ge=1, le=100),
        search_type: Optional[str] = Query(None, pattern="^(classic|targeted)$"),
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение истории поисковых сессий текущего пользователя
    """
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        return await search_service.get_search_history(keycloak_id, limit, search_type)
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_search_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/session/{session_id}",
    response_model=SearchSessionInfo,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_session(
        session_id: int,
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение конкретной поисковой сессии по ID
    """
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        return await search_service.get_search_session(session_id, keycloak_id)
    except SearchSessionNotFoundException:
        raise HTTPException(status_code=404, detail="Search session not found")
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_search_session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/profiles/count",
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_profiles_count(
        search_service: SearchService = Depends(get_search_service),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение общего количества профилей в системе
    """
    try:
        count = await search_service.get_profiles_count()
        return {"total_profiles": count}
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_profiles_count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def delete_old_search_history(
        older_than_days: int = Query(30, ge=1, le=365),
        search_service: SearchService = Depends(get_search_service), 
        current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление старой истории поиска текущего пользователя
    """
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            logger.error(f"Keycloak ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        await search_service.delete_search_history(keycloak_id, older_than_days)
        return None
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in delete_old_search_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")