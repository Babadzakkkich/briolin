from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.services.matching_service import MatchingService
from app.dependencies import get_matching_service
from app.core.logger import logger

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get(
    "/matches/{match_id}/answers",
    summary="Внутренний: Получение матча с ответами"
)
async def get_internal_match_answers(
    match_id: int,
    user_id: str = Query(..., description="Keycloak ID пользователя"),
    service: MatchingService = Depends(get_matching_service)
):
    """
    Внутренний эндпоинт для chat-service.
    Возвращает ответы на вопросы для матча без проверки авторизации.
    """
    match = await service.get_match_with_answers(
        match_id=match_id,
        user_id=user_id
    )
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")
    return match


@router.get(
    "/matches/{match_id}/exists",
    summary="Внутренний: Проверка существования матча"
)
async def check_match_exists(
    match_id: int,
    user_id: str = Query(..., description="Keycloak ID пользователя"),
    service: MatchingService = Depends(get_matching_service)
):
    """Проверка существования матча для пользователя"""
    match = await service.get_match_with_answers(
        match_id=match_id,
        user_id=user_id
    )
    return {"exists": match is not None}