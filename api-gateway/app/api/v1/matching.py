from fastapi import APIRouter, Depends, Query, HTTPException, Response, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from app.services.http_client import http_client
from app.schemas.matching import (
    SwipeRequest,
    SwipeResponse,
    SwipeStatusResponse,
    MatchResponse,
    RecommendationProfile,
    ResetSwipesResponse
)
from shared.schemas.shared import Gender

router = APIRouter(prefix="/matching", tags=["Matching"])
security = HTTPBearer(auto_error=False)


# ========== SWIPE ENDPOINTS ==========

@router.post(
    "/swipe",
    response_model=SwipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Свайп (лайк/дизлайк)"
)
async def create_swipe(
    request: Request,
    swipe_data: SwipeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)  # не используется, но нужна для совместимости
):
    """Создание свайпа (лайк или дизлайк)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/swipe/status/{target_user_id}",
    response_model=SwipeStatusResponse,
    summary="Статус свайпа к пользователю"
)
async def get_swipe_status(
    target_user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение статуса свайпа к конкретному пользователю"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== MATCHES ENDPOINTS ==========

@router.get(
    "/matches",
    response_model=List[MatchResponse],
    summary="Список матчей"
)
async def get_matches(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка матчей текущего пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== RECOMMENDATIONS ENDPOINTS ==========

@router.get(
    "/recommendations/classic",
    response_model=List[RecommendationProfile],
    summary="Классические рекомендации"
)
async def get_classic_recommendations(
    request: Request,
    limit: int = Query(20, ge=1, le=50, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100),
    max_age: Optional[int] = Query(None, ge=18, le=100),
    city: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение классических рекомендаций"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/recommendations/targeted",
    response_model=List[RecommendationProfile],
    summary="Таргетированные рекомендации"
)
async def get_targeted_recommendations(
    request: Request,
    limit: int = Query(20, ge=1, le=50, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100),
    max_age: Optional[int] = Query(None, ge=18, le=100),
    city: Optional[str] = None,
    education: Optional[str] = None,
    hobbies_keywords: Optional[List[str]] = Query(None, description="Список ключевых слов интересов"),
    online_only: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение таргетированных рекомендаций"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== ADMIN ENDPOINTS ==========

@router.delete(
    "/admin/swipes/reset",
    response_model=ResetSwipesResponse,
    status_code=status.HTTP_200_OK,
    summary="Сброс свайпов пользователя (админ)"
)
async def reset_user_swipes(
    request: Request,
    user_id: str = Query(..., description="Keycloak ID пользователя для сброса свайпов"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Сброс свайпов пользователя (только для администраторов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )