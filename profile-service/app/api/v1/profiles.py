from fastapi import APIRouter, Depends, HTTPException, status
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    BasicProfileCreate, DetailedProfileCreate, FullProfileUpdate,
    FullProfileResponse
)
from app.schemas.questions import ProfileQuestionsCreate, ProfileQuestionsUpdate, ProfileQuestionsResponse
from app.dependencies import get_profile_service, get_current_user
from app.core.logger import logger
from app.core.exceptions import PermissionDeniedException, ProfileNotFoundException, ProfileAlreadyExistsException

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("/saga/{saga_id}/status")
async def get_saga_status(
    saga_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """Получение статуса операции по ID саги"""
    status = await service.get_saga_status(saga_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Saga not found")
    return status

@router.post("/basic", status_code=status.HTTP_201_CREATED, response_model=FullProfileResponse)
async def create_basic_profile(
    profile_data: BasicProfileCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """
    СИНХРОННОЕ создание базового профиля
    Возвращает созданный профиль
    """
    try:
        result = await service.create_basic_profile(
            keycloak_id=current_user["keycloak_id"],
            basic_data=profile_data,
            current_user=current_user
        )
        return result
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ProfileAlreadyExistsException as e:
        # Если профиль уже существует, возвращаем его с кодом 200
        return result
    except Exception as e:
        logger.error(f"Failed to create basic profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detailed", status_code=status.HTTP_201_CREATED, response_model=FullProfileResponse)
async def create_detailed_profile(
    profile_data: DetailedProfileCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """
    СИНХРОННОЕ создание детального профиля
    Возвращает полный профиль
    """
    try:
        result = await service.create_detailed_profile(
            keycloak_id=current_user["keycloak_id"],
            detailed_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create detailed profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post(
    "/me/questions",
    status_code=status.HTTP_201_CREATED,
    response_model=FullProfileResponse
)
async def set_my_questions(
    questions_data: ProfileQuestionsCreate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Создание или полное обновление вопросов профиля"""
    try:
        result = await service.set_questions(
            keycloak_id=current_user["keycloak_id"],
            questions_data=questions_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to set questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение своего полного профиля"""
    try:
        profile = await service.get_full_profile_by_keycloak_id(current_user["keycloak_id"])
        return profile
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/me/questions",
    response_model=ProfileQuestionsResponse
)
async def get_my_questions(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение своих вопросов"""
    questions = await service.get_questions(current_user["keycloak_id"])
    if not questions:
        raise HTTPException(status_code=404, detail="Questions not set")
    return questions


@router.get("/me/questions/status")
async def get_my_questions_status(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Проверка статуса заполнения вопросов"""
    questions = await service.get_questions(current_user["keycloak_id"])
    
    has_questions = False
    questions_count = 0
    if questions:
        questions_dict = {
            "question_1": questions.question_1,
            "question_2": questions.question_2,
            "question_3": questions.question_3,
            "question_4": questions.question_4,
            "question_5": questions.question_5,
        }
        questions_count = sum(1 for v in questions_dict.values() if v and v.strip())
        has_questions = questions_count == 5
    
    return {
        "has_questions": has_questions,
        "questions_count": questions_count,
        "total_required": 5,
        "can_receive_likes": has_questions
    }


@router.get(
    "/{keycloak_id}/questions",
    response_model=ProfileQuestionsResponse
)
async def get_user_questions(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение вопросов другого пользователя (перед лайком)"""
    questions = await service.get_questions(keycloak_id)
    if not questions:
        raise HTTPException(status_code=404, detail="User has no questions")
    return questions

@router.put("/me", status_code=status.HTTP_202_ACCEPTED)
async def update_my_profile(
    profile_data: FullProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ обновление своего полного профиля"""
    try:
        result = await service.update_full_profile(
            keycloak_id=current_user["keycloak_id"],
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch(
    "/me/questions",
    response_model=FullProfileResponse
)
async def update_my_questions(
    questions_data: ProfileQuestionsUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Частичное обновление вопросов профиля"""
    try:
        result = await service.update_questions(
            keycloak_id=current_user["keycloak_id"],
            questions_data=questions_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ удаление своего полного профиля"""
    try:
        result = await service.delete_full_profile(
            keycloak_id=current_user["keycloak_id"],
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{keycloak_id}", response_model=FullProfileResponse)
async def get_profile_by_id(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Получение профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        profile = await service.get_full_profile_by_keycloak_id(keycloak_id)
        return profile
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_profile_by_id(
    keycloak_id: str,
    profile_data: FullProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ обновление профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        result = await service.update_full_profile(
            keycloak_id=keycloak_id,
            profile_data=profile_data,
            current_user=current_user
        )
        return result
    except ProfileNotFoundException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{keycloak_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_profile_by_id(
    keycloak_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """АСИНХРОННОЕ удаление профиля по Keycloak ID (только для админов)"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        result = await service.delete_full_profile(
            keycloak_id=keycloak_id,
            current_user=current_user
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))