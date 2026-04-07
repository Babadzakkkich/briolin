from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List

from app.services.matching_service import MatchingService
from app.dependencies import get_matching_service, require_admin
from app.schemas.swipe import SwipeRequest, SwipeResponse, SwipeStatusResponse
from app.schemas.match import MatchResponse
from app.schemas.recommendation import (
    ClassicRecommendationFilters,
    TargetedRecommendationFilters,
    RecommendationListResponse
)
from app.schemas.lock import TargetedSearchLockInfo
from app.core.exceptions import (
    SwipeLimitExceededException,
    AlreadySwipedException,
    UserNotFoundException,
    TargetedSearchLockedException
)
from shared.auth.dependencies import get_current_user
from shared.schemas.shared import Gender

router = APIRouter(prefix="/matching", tags=["Matching"])


# ========== SWIPE ENDPOINTS ==========

@router.post("/swipe", response_model=SwipeResponse, status_code=status.HTTP_200_OK)
async def create_swipe(
    request: SwipeRequest,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Создание свайпа (лайк или дизлайк)"""
    try:
        return await service.swipe(
            from_user_id=current_user["keycloak_id"],
            to_user_id=request.target_user_id,
            action=request.action
        )
    except SwipeLimitExceededException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except AlreadySwipedException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except UserNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/swipe/status/{target_user_id}", response_model=SwipeStatusResponse)
async def get_swipe_status(
    target_user_id: str,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Проверяет, свайпал ли текущий пользователь на указанного"""
    return await service.get_swipe_status(current_user["keycloak_id"], target_user_id)


# ========== MATCHES ENDPOINTS ==========

@router.get("/matches", response_model=List[MatchResponse])
async def get_matches(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Возвращает список всех матчей текущего пользователя"""
    matches, total = await service.get_matches(current_user["keycloak_id"], page, limit)
    return matches


# ========== RECOMMENDATIONS ENDPOINTS ==========

@router.get("/recommendations/classic", response_model=RecommendationListResponse)
async def classic_recommendations(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100, description="Минимальный возраст"),
    max_age: Optional[int] = Query(None, ge=18, le=100, description="Максимальный возраст"),
    city: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Классические рекомендации на основе базовых фильтров (с пагинацией)"""
    filters = ClassicRecommendationFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        city=city
    )
    return await service.get_classic_recommendations(
        user_id=current_user["keycloak_id"],
        filters=filters,
        page=page,
        limit=limit
    )


@router.get("/recommendations/targeted", response_model=RecommendationListResponse)
async def targeted_recommendations(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100, description="Минимальный возраст"),
    max_age: Optional[int] = Query(None, ge=18, le=100, description="Максимальный возраст"),
    city: Optional[str] = None,
    education: Optional[str] = None,
    hobbies_keywords: Optional[List[str]] = Query(None, description="Список ключевых слов интересов"),
    online_only: bool = False,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Таргетированные рекомендации на основе семантической близости (эмбеддингов) с учётом блокировки по свайпам"""
    filters = TargetedRecommendationFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        city=city,
        education=education,
        hobbies_keywords=hobbies_keywords,
        online_only=online_only
    )
    try:
        return await service.get_targeted_recommendations(
            user_id=current_user["keycloak_id"],
            filters=filters,
            page=page,
            limit=limit
        )
    except TargetedSearchLockedException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "unlock_time": e.unlock_time.isoformat() if e.unlock_time else None,
                "time_until_unlock": e.time_until_unlock,
                "swipes_used": e.swipes_used,
                "daily_limit": e.daily_limit
            }
        )


# ========== LOCK STATUS ENDPOINT ==========

@router.get("/lock-status", response_model=TargetedSearchLockInfo)
async def get_lock_status(
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Получение статуса блокировки таргетированных рекомендаций для текущего пользователя"""
    return await service.get_lock_status(current_user["keycloak_id"])


# ========== ADMIN ENDPOINTS ==========

@router.delete("/admin/swipes/reset", status_code=status.HTTP_200_OK)
async def reset_swipes(
    user_id: str = Query(..., description="Keycloak ID пользователя для сброса свайпов"),
    _: dict = Depends(require_admin()),
    service: MatchingService = Depends(get_matching_service)
):
    """Удаляет все свайпы указанного пользователя и сбрасывает блокировку. Только для администраторов."""
    deleted = await service.reset_swipes(user_id)
    return {"message": f"Удалено {deleted} записей свайпов для пользователя {user_id}"}