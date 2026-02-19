from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import (
    SearchRequest,
    TargetedSearchRequest,
    SearchResponse,
    SearchSessionResponse,
    SearchLockInfoResponse,
    ErrorResponse
)
from app.services.search import SearchService
from app.database.session import own_session_factory, profile_session_factory
from app.core.exceptions import SearchServiceException, SearchLockedException, SearchSessionNotFoundException
from app.core.logger import logger
from shared.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/search", tags=["Search"])


async def get_own_db() -> AsyncSession:
    """Dependency for getting own database session (search_sessions)"""
    async with own_session_factory() as session:
        yield session


async def get_profile_db() -> AsyncSession:
    """Dependency for getting profile database session (read-only)"""
    async with profile_session_factory() as session:
        yield session


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
        search_request: SearchRequest,
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Выполняет классический поиск по профилям
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        return await search_service.classic_search(
            user_id=user_id,
            gender=search_request.gender,
            min_age=search_request.min_age,
            max_age=search_request.max_age,
            city=search_request.city,
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
        search_request: TargetedSearchRequest,
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Выполняет таргетированный поиск с использованием detailed_profiles
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        return await search_service.targeted_search(
            user_id=user_id,
            search_params=search_request
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
    response_model=SearchLockInfoResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_lock_status(
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение статуса блокировки таргетированного поиска для текущего пользователя
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        return await search_service.get_search_lock_status(user_id)
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_search_lock_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/history",
    response_model=List[SearchSessionResponse],
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_history(
        limit: int = Query(50, ge=1, le=100),
        search_type: Optional[str] = Query(None, pattern="^(classic|targeted)$"),
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение истории поисковых сессий текущего пользователя
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        return await search_service.get_search_history(user_id, limit, search_type)
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_search_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/session/{session_id}",
    response_model=SearchSessionResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_session(
        session_id: int,
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение конкретной поисковой сессии по ID
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        session = await search_service.get_search_session(session_id)

        # Проверяем, что сессия принадлежит текущему пользователю
        if session.user_id != user_id:
            logger.warning(f"Session {session_id} belongs to another user")
            raise HTTPException(status_code=403, detail="Cannot view session of another user")

        return session
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
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Получение общего количества профилей в системе
    """
    try:
        search_service = SearchService(own_db, profile_db)
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
        own_db: AsyncSession = Depends(get_own_db),
        profile_db: AsyncSession = Depends(get_profile_db),
        current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление старой истории поиска текущего пользователя
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"User ID not found in token: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid user data in token")

        search_service = SearchService(own_db, profile_db)
        await search_service.delete_search_history(user_id, older_than_days)
        return None
    except SearchServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in delete_old_search_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")