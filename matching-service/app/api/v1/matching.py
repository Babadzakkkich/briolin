from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List

from app.services.matching_service import MatchingService
from app.dependencies import get_matching_service, require_admin
from app.schemas.swipe import (
    SwipeResponse, SwipeStatusResponse,
    LikeRequest, DislikeRequest
)
from app.schemas.match import MatchResponse
from app.schemas.search import (
    ClassicSearchFilters,
    TargetedSearchFilters,
    SearchListResponse
)
from app.schemas.recommendation import (
    TargetedRecommendationFilters,
    RecommendationListResponse
)
from app.schemas.lock import TargetedSearchLockInfo, LikeUsageInfo
from app.core.exceptions import (
    LikeLimitExceededException,
    AlreadySwipedException,
    UserNotFoundException,
    TargetedSearchLockedException
)
from shared.auth.dependencies import get_current_user
from shared.schemas.shared import Gender

router = APIRouter(prefix="/matching", tags=["Matching"])


# ========== LIKE/DISLIKE ENDPOINTS ==========

@router.post("/like", response_model=SwipeResponse, status_code=status.HTTP_200_OK)
async def like_profile(
    request: LikeRequest,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Поставить лайк профилю (с проверкой дневного лимита)"""
    try:
        return await service.like_profile(
            from_user_id=current_user["keycloak_id"],
            to_user_id=request.target_user_id
        )
    except LikeLimitExceededException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "likes_used": e.likes_used,
                "daily_limit": e.daily_limit
            }
        )
    except AlreadySwipedException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except UserNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/dislike", response_model=SwipeResponse, status_code=status.HTTP_200_OK)
async def dislike_profile(
    request: DislikeRequest,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Поставить дизлайк профилю (без ограничений)"""
    try:
        return await service.dislike_profile(
            from_user_id=current_user["keycloak_id"],
            to_user_id=request.target_user_id
        )
    except AlreadySwipedException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except UserNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/like-usage", response_model=LikeUsageInfo)
async def get_like_usage(
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Получение информации об использовании лайков"""
    return await service.get_like_usage(current_user["keycloak_id"])


# ========== SWIPE ENDPOINTS ==========

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


# ========== SEARCH ENDPOINTS ==========

@router.get("/search/classic", response_model=SearchListResponse)
async def classic_search(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100, description="Минимальный возраст"),
    max_age: Optional[int] = Query(None, ge=18, le=100, description="Максимальный возраст"),
    city: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Классический поиск на основе базовых фильтров (с пагинацией)"""
    filters = ClassicSearchFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        city=city
    )
    return await service.classic_search(
        user_id=current_user["keycloak_id"],
        filters=filters,
        page=page,
        limit=limit
    )


@router.get("/search/targeted", response_model=SearchListResponse)
async def targeted_search(
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
    """Таргетированный поиск с расширенными фильтрами (без эмбеддингов, без блокировки)"""
    filters = TargetedSearchFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        city=city,
        education=education,
        hobbies_keywords=hobbies_keywords,
        online_only=online_only
    )
    return await service.targeted_search(
        user_id=current_user["keycloak_id"],
        filters=filters,
        page=page,
        limit=limit
    )


# ========== RECOMMENDATIONS ENDPOINTS ==========

@router.get("/recommendations/targeted", response_model=RecommendationListResponse)
async def targeted_recommendations(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    city: Optional[str] = Query(None, description="Город (если не указан - используется город пользователя)"),
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """
    Таргетированные рекомендации на основе эмбеддингов с автоматическими фильтрами.
    
    **Автоматически определяются:**
    - **Пол**: противоположный полу пользователя (для OTHER - все)
    - **Возраст**: ±5 лет от возраста пользователя (автоматически расширяется)
    - **Город**: можно указать вручную, иначе используется город пользователя
    
    **Блокировка:** Дневной лимит просмотров (100), после превышения - блокировка на 12 часов.
    """
    filters = TargetedRecommendationFilters(city=city)
    
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
                "profiles_viewed": e.profiles_viewed,
                "daily_limit": e.daily_limit
            }
        )


# ========== LOCK STATUS ENDPOINT ==========

@router.get("/lock-status", response_model=TargetedSearchLockInfo)
async def get_lock_status(
    current_user: dict = Depends(get_current_user),
    service: MatchingService = Depends(get_matching_service)
):
    """Получение статуса блокировки таргетированных рекомендаций (эмбеддинги)"""
    return await service.get_targeted_lock_status(current_user["keycloak_id"])


# ========== ADMIN ENDPOINTS ==========

@router.delete("/admin/reset/{user_id}", status_code=status.HTTP_200_OK)
async def reset_user_data(
    user_id: str,
    _: dict = Depends(require_admin()),
    service: MatchingService = Depends(get_matching_service)
):
    """
    Сброс всех данных пользователя (свайпы, блокировки, лайки).
    Только для администраторов.
    """
    result = await service.reset_user_data(user_id)
    return {
        "message": f"Данные пользователя {user_id} сброшены",
        "swipes_deleted": result["swipes_deleted"]
    }