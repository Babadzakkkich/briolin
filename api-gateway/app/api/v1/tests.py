from typing import Optional
import uuid
from fastapi import APIRouter, Request, Depends, Response, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.http_client import http_client
from app.schemas.test import (
    TestStartRequest,
    TestStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    TestCompleteRequest,
    TestCompleteResponse,
    TestResultsResponse,
    TestHistoryResponse,
    UserStatisticsResponse,
    AdminQuestionResponse,
    ErrorResponse
)

router = APIRouter(prefix="/tests", tags=["Tests"])
security = HTTPBearer(auto_error=False)

@router.post(
    "/start",
    status_code=status.HTTP_201_CREATED,
    response_model=TestStartResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def start_test(
    test_data: TestStartRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Начать новый тест"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post(
    "/{session_id}/answers/{question_id}",
    response_model=AnswerSubmitResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def submit_answer(
    session_id: uuid.UUID,
    question_id: str,
    answer_data: AnswerSubmitRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Сохранить ответ на вопрос"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post(
    "/{session_id}/complete",
    response_model=TestCompleteResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def complete_test(
    session_id: uuid.UUID,
    complete_data: TestCompleteRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Завершить тест и получить результаты"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/{session_id}/results",
    response_model=TestResultsResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_results(
    session_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить результаты теста"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/history",
    response_model=TestHistoryResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_test_history(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить историю тестов пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/statistics",
    response_model=UserStatisticsResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_user_statistics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить статистику пользователя по тестам"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/questions/{question_id}",
    response_model=AdminQuestionResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_question(
    question_id: str,
    request: Request,
    include_correct_answers: bool = Query(False, description="Include correct answers (admin only)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить вопрос по ID (для админов или для продолжения теста)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )