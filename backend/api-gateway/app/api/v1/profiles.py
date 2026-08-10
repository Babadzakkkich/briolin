from fastapi import APIRouter, Request, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.http_client import http_client
from app.schemas.profile import (
    BasicProfileCreate,
    DetailedProfileCreate,
    FullProfileUpdate,
    FullProfileResponse,
    ProfileQuestionsCreate,
    ProfileQuestionsResponse,
    ProfileQuestionsUpdate,
    SagaStatusResponse,
    AsyncOperationResponse
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])
security = HTTPBearer(auto_error=False)

@router.get("/saga/{saga_id}/status", response_model=SagaStatusResponse)
async def get_saga_status(
    saga_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение статуса операции по ID саги"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post(
    "/basic", 
    status_code=status.HTTP_201_CREATED,
    response_model=FullProfileResponse
)
async def create_basic_profile(
    profile_data: BasicProfileCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """СИНХРОННОЕ создание базового профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/detailed", 
    status_code=status.HTTP_201_CREATED,
    response_model=FullProfileResponse
)
async def create_detailed_profile(
    profile_data: DetailedProfileCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """СИНХРОННОЕ создание детального профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.post(
    "/me/questions",
    status_code=status.HTTP_201_CREATED,
    response_model=FullProfileResponse,
    summary="Создать вопросы профиля",
    description="Создание или полное обновление 5 вопросов для знакомства."
)
async def set_my_questions(
    questions_data: ProfileQuestionsCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Создание или обновление вопросов профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/me/questions",
    response_model=ProfileQuestionsResponse,
    summary="Мои вопросы",
    description="Получение своих вопросов для знакомства."
)
async def get_my_questions(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение своих вопросов"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/me/questions/status",
    summary="Статус вопросов",
    description="Проверка, заполнены ли все вопросы профиля."
)
async def get_my_questions_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Проверка статуса вопросов"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/{keycloak_id}/questions",
    response_model=ProfileQuestionsResponse,
    summary="Вопросы пользователя",
    description="Получение вопросов другого пользователя (перед лайком)."
)
async def get_user_questions(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение вопросов пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put(
    "/me", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def update_my_profile(
    profile_data: FullProfileUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ обновление своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.patch(
    "/me/questions",
    response_model=FullProfileResponse,
    summary="Обновить вопросы профиля",
    description="Частичное обновление вопросов профиля."
)
async def update_my_questions(
    questions_data: ProfileQuestionsUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Частичное обновление вопросов"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete(
    "/me", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def delete_my_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ удаление своего полного профиля"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/{keycloak_id}", response_model=FullProfileResponse)
async def get_profile_by_id(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.put(
    "/{keycloak_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def update_profile_by_id(
    keycloak_id: str,
    profile_data: FullProfileUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ обновление профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete(
    "/{keycloak_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncOperationResponse
)
async def delete_profile_by_id(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """АСИНХРОННОЕ удаление профиля по Keycloak ID (только для админов)"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )