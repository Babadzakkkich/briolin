from fastapi import APIRouter, Depends, Query, HTTPException, Response, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from app.services.http_client import http_client
from app.schemas.matching import (
    LikeRequest,
    DislikeRequest,
    LikeUsageInfo,
    SwipeRequest,
    SwipeResponse,
    SwipeStatusResponse,
    MatchResponse,
    SearchListResponse,
    RecommendationListResponse,
    TargetedSearchLockInfo,
    ResetUserDataResponse,
    LikeLimitErrorResponse,
    TargetedSearchLockedErrorResponse
)
from shared.schemas.shared import Gender

router = APIRouter(prefix="/matching", tags=["Matching"])
security = HTTPBearer(auto_error=False)


# ========== LIKE/DISLIKE ENDPOINTS ==========

@router.post(
    "/like",
    response_model=SwipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Лайкнуть профиль",
    description="Поставить лайк профилю. Действует дневной лимит лайков.",
    responses={
        200: {"description": "Лайк успешно поставлен"},
        400: {"description": "Неверные параметры запроса"},
        401: {"description": "Не авторизован"},
        404: {"description": "Пользователь не найден"},
        409: {"description": "Уже был совершён свайп на этого пользователя"},
        429: {"description": "Дневной лимит лайков исчерпан", "model": LikeLimitErrorResponse}
    }
)
async def like_profile(
    request: Request,
    like_data: LikeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Поставить лайк профилю (с проверкой дневного лимита)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/dislike",
    response_model=SwipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Дизлайкнуть профиль",
    description="Поставить дизлайк профилю. Без ограничений.",
    responses={
        200: {"description": "Дизлайк успешно поставлен"},
        400: {"description": "Неверные параметры запроса"},
        401: {"description": "Не авторизован"},
        404: {"description": "Пользователь не найден"},
        409: {"description": "Уже был совершён свайп на этого пользователя"}
    }
)
async def dislike_profile(
    request: Request,
    dislike_data: DislikeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Поставить дизлайк профилю (без ограничений)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/like-usage",
    response_model=LikeUsageInfo,
    summary="Статистика использования лайков",
    description="Возвращает информацию об использовании лайков текущим пользователем за сегодня."
)
async def get_like_usage(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение информации об использовании лайков"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== SWIPE ENDPOINTS (для обратной совместимости) ==========

@router.post(
    "/swipe",
    response_model=SwipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Свайп (лайк/дизлайк)",
    description="Создание свайпа. Для действия 'like' проверяется дневной лимит.",
    deprecated=True
)
async def create_swipe(
    request: Request,
    swipe_data: SwipeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Создание свайпа (лайк или дизлайк).
    **Устаревший метод**, используйте `/like` и `/dislike`.
    """
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


# ========== SEARCH ENDPOINTS ==========

@router.get(
    "/search/classic",
    response_model=SearchListResponse,
    summary="Классический поиск",
    description="Поиск профилей по базовым фильтрам (пол, возраст, город). Без ограничений."
)
async def classic_search(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100, description="Минимальный возраст"),
    max_age: Optional[int] = Query(None, ge=18, le=100, description="Максимальный возраст"),
    city: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Классический поиск на основе базовых фильтров (с пагинацией)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/search/targeted",
    response_model=SearchListResponse,
    summary="Таргетированный поиск",
    description="Расширенный поиск профилей по фильтрам (образование, интересы, онлайн). Без ограничений."
)
async def targeted_search(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    gender: Optional[Gender] = None,
    min_age: Optional[int] = Query(None, ge=18, le=100, description="Минимальный возраст"),
    max_age: Optional[int] = Query(None, ge=18, le=100, description="Максимальный возраст"),
    city: Optional[str] = None,
    education: Optional[str] = None,
    hobbies_keywords: Optional[List[str]] = Query(None, description="Список ключевых слов интересов"),
    online_only: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Таргетированный поиск с расширенными фильтрами (без эмбеддингов, без блокировки)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== RECOMMENDATIONS ENDPOINTS (ЭМБЕДДИНГИ) ==========

@router.get(
    "/recommendations/targeted",
    response_model=RecommendationListResponse,
    summary="Таргетированные рекомендации (эмбеддинги)",
    description="""
    Премиум-рекомендации на основе семантической близости с автоматическими фильтрами.
    
    **Автоматически определяются:**
    - **Пол**: противоположный полу пользователя (для OTHER - все)
    - **Возраст**: ±5 лет от возраста пользователя (автоматически расширяется)
    - **Город**: можно указать вручную, иначе используется город пользователя
    
    **Блокировка:** Дневной лимит просмотров, после превышения - временная блокировка.
    """,
    responses={
        200: {"description": "Успешный ответ"},
        401: {"description": "Не авторизован"},
        429: {"description": "Дневной лимит просмотров исчерпан", "model": TargetedSearchLockedErrorResponse}
    }
)
async def targeted_recommendations(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
    city: Optional[str] = Query(None, description="Город (если не указан - используется город пользователя)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Таргетированные рекомендации на основе эмбеддингов с автоматическими фильтрами.
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== LOCK STATUS ENDPOINT ==========

@router.get(
    "/lock-status",
    response_model=TargetedSearchLockInfo,
    summary="Статус блокировки таргетированных рекомендаций"
)
async def get_lock_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение статуса блокировки таргетированных рекомендаций (эмбеддинги) для текущего пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# ========== ADMIN ENDPOINTS ==========

@router.delete(
    "/admin/reset/{user_id}",
    response_model=ResetUserDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Сброс данных пользователя (админ)"
)
async def reset_user_data(
    user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Сброс всех данных пользователя (свайпы, блокировки, лайки).
    Только для администраторов.
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )