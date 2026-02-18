from fastapi import APIRouter, Request, Depends, Response, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from app.services.http_client import http_client
from app.schemas.search import (
    SearchRequest,
    TargetedSearchRequest,
    SearchResponse,
    SearchSessionResponse,
    SearchLockInfoResponse,  # ДОБАВЛЕНО
    ErrorResponse
)

router = APIRouter(prefix="/search", tags=["Search"])
security = HTTPBearer(auto_error=False)


@router.post(
    "/classic/{user_id}",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def classic_search(
        user_id: int,
        search_request: SearchRequest,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Выполняет классический поиск по профилям"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/targeted/{user_id}",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},  # ДОБАВЛЕНО - Too Many Requests
        500: {"model": ErrorResponse}
    }
)
async def targeted_search(
        user_id: int,
        search_request: TargetedSearchRequest,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Выполняет таргетированный поиск с использованием detailed_profiles"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/lock-status/{user_id}",  # НОВЫЙ ЭНДПОИНТ
    response_model=SearchLockInfoResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_lock_status(
        user_id: int,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получение статуса блокировки таргетированного поиска для пользователя

    - **user_id**: ID пользователя
    - Возвращает информацию о блокировке: заблокирован ли поиск,
      сколько профилей просмотрено, когда разблокируется
    """
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/history/{user_id}",
    response_model=List[SearchSessionResponse],
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_search_history(
        user_id: int,
        request: Request,
        limit: int = Query(50, ge=1, le=100),
        search_type: Optional[str] = Query(None, regex="^(classic|targeted)$"),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение истории поисковых сессий пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


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
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение конкретной поисковой сессии по ID"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/profiles/count",
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_profiles_count(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение общего количества профилей в системе"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.delete(
    "/history/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def delete_old_search_history(
        user_id: int,
        request: Request,
        older_than_days: int = Query(30, ge=1, le=365),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление старой истории поиска пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )