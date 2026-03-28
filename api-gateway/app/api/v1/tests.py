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
    UserTestStatistics,
    AdminQuestionResponse,
    ErrorResponse,
    CurrentTestResponse,
    ActiveTestErrorResponse
)
from app.core.logger import logger

router = APIRouter(prefix="/tests", tags=["Tests"])
security = HTTPBearer(auto_error=False)


@router.get(
    "/current",
    response_model=CurrentTestResponse,
    responses={
        200: {"description": "Current test session data"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"description": "No active test session"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get current test",
    description="""
    Возвращает информацию о текущем активном тесте пользователя.
    
    Если у пользователя есть активная сессия теста, возвращает:
    - Данные теста (название, описание)
    - Вопросы с уже сохраненными ответами
    - Оставшееся время
    - Прогресс прохождения
    
    Если активной сессии нет, возвращает 404.
    
    Это позволяет пользователю продолжить тест после прерывания.
    """
)
async def get_current_test(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current active test for the user"""
    try:
        response = await http_client.proxy_request(request)
        
        if response.status_code == 404:
            # Проксируем 404 как есть
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error getting current test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current test"
        )


@router.post(
    "/start",
    status_code=status.HTTP_201_CREATED,
    response_model=TestStartResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        409: {"model": ActiveTestErrorResponse, "description": "Active test session already exists"},
        429: {"model": ErrorResponse, "description": "Daily limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Start new test",
    description="""
    Начинает новый тест для пользователя.
    
    **Важно:** Пользователь может иметь только одну активную сессию теста.
    Если активная сессия уже существует, возвращается ошибка 409 с ID существующей сессии.
    
    Для продолжения существующего теста используйте GET /tests/current
    """
)
async def start_test(
    test_data: TestStartRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start a new test for the user"""
    try:
        response = await http_client.proxy_request(request)
        
        # Если testing-service вернул 409, проксируем ответ с деталями
        if response.status_code == 409:
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start test"
        )


@router.post(
    "/{session_id}/answers/{question_id}",
    response_model=AnswerSubmitResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid answer format"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Test session or question not found"},
        409: {"model": ErrorResponse, "description": "Test already completed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Submit answer",
    description="Сохраняет ответ пользователя на вопрос теста"
)
async def submit_answer(
    session_id: uuid.UUID,
    question_id: str,
    answer_data: AnswerSubmitRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Save user's answer to a test question"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )


@router.post(
    "/{session_id}/complete",
    response_model=TestCompleteResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Test time limit exceeded or invalid state"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Test session not found"},
        409: {"model": ErrorResponse, "description": "Test already completed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Complete test",
    description="Завершает тест, подсчитывает результаты и возвращает их"
)
async def complete_test(
    session_id: uuid.UUID,
    complete_data: TestCompleteRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Complete the test and get results"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error completing test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete test"
        )


@router.get(
    "/{session_id}/results",
    response_model=TestResultsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Test session or results not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get test results",
    description="Возвращает результаты завершенного теста"
)
async def get_results(
    session_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get results of a completed test"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get test results"
        )


@router.get(
    "/history",
    response_model=TestHistoryResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Test history",
    description="Возвращает историю пройденных тестов пользователя с пагинацией"
)
async def get_test_history(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's test history with pagination"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error getting test history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get test history"
        )


@router.get(
    "/statistics",
    response_model=UserTestStatistics,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Test statistics",
    description="Возвращает статистику прохождения тестов пользователем"
)
async def get_user_statistics(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's test statistics"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.get(
    "/questions/{question_id}",
    response_model=AdminQuestionResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Question not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get question",
    description="Возвращает вопрос по ID. Для обычных пользователей скрывает правильные ответы."
)
async def get_question(
    question_id: str,
    request: Request,
    include_correct_answers: bool = Query(False, description="Include correct answers (admin only)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get question by ID (hides correct answers for non-admin users)"""
    try:
        response = await http_client.proxy_request(request)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question"
        )