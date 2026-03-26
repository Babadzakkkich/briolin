from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.testing_service import TestingService
from app.dependencies import get_testing_service, get_current_user
from app.core.exceptions import TestingException
from app.core.logger import logger
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
    test_data: TestStartRequest = Body(...),
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Начать новый тест"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        result = await service.start_new_test(keycloak_id)
        return result
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{session_id}/answers/{question_id}",
    response_model=AnswerSubmitResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def submit_answer(
    session_id: uuid.UUID,
    question_id: str,
    answer_data: AnswerSubmitRequest,
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Сохранить ответ на вопрос"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        result = await service.submit_answer(
            session_id=session_id,
            keycloak_id=keycloak_id,
            question_id=question_id,
            answer=answer_data.answer
        )
        return result
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{session_id}/complete",
    response_model=TestCompleteResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def complete_test(
    session_id: uuid.UUID,
    complete_data: TestCompleteRequest = Body(...),
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)  # Это ваша функция
):
    """Завершить тест и получить результаты"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        user_email = current_user.get("email")           # email из токена
        user_name = current_user.get("username") or current_user.get("name") or "User"
        
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        result = await service.complete_test(
            session_id=session_id,
            keycloak_id=keycloak_id,
            user_email=user_email,
            user_name=user_name
        )
        return result
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error completing test: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{session_id}/results",
    response_model=TestResultsResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_results(
    session_id: uuid.UUID,
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Получить результаты теста"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        result = await service.get_test_results(session_id, keycloak_id)
        return result
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/history",
    response_model=TestHistoryResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_test_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Получить историю тестов пользователя"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        history = await service.get_user_test_history(keycloak_id, skip, limit)
        return history
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting test history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/statistics",
    response_model=UserTestStatistics,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_user_statistics(
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Получить статистику пользователя по тестам"""
    try:
        keycloak_id = current_user.get("keycloak_id")
        if not keycloak_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        stats = await service.get_user_statistics(keycloak_id)
        return stats
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/questions/{question_id}",
    response_model=AdminQuestionResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_question(
    question_id: str,
    include_correct_answers: bool = Query(False, description="Include correct answers (admin only)"),
    service: TestingService = Depends(get_testing_service),
    current_user: dict = Depends(get_current_user)
):
    """Получить вопрос по ID (для админов или для продолжения теста)"""
    try:
        from app.services.test_generator import get_test_generator
        generator = get_test_generator()
        
        question = await generator.get_question_by_id(question_id)
        question_dict = question.dict()
        
        # Убираем правильные ответы, если не админ
        if not include_correct_answers:
            user_roles = current_user.get("roles", [])
            if "admin" not in user_roles:
                if "options" in question_dict:
                    for option in question_dict["options"]:
                        if "score_impact" in option:
                            del option["score_impact"]
                        if "is_correct" in option:
                            del option["is_correct"]
        
        return AdminQuestionResponse(**question_dict)
        
    except TestingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")