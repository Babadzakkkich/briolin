import uuid
from typing import List, Optional

from app.core.logger import logger
from app.schemas.chat import (
    BulkMessageIdsRequest,
    ChatCreate,
    ChatListResponse,
    ChatResponse,
    ChatUpdate,
    MessageCreate,
    MessageIdsRequest,
    MessageListResponse,
    MessageReadStatusResponse,
    MessageResponse,
    MessageUpdate,
    OnlineUsersResponse,
    ReadByUserInfo,
    SearchMessagesResponse,
)
from app.services.http_client import http_client
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/chats", tags=["Chats"])
security = HTTPBearer(auto_error=False)


@router.get(
    "/search/messages",
    response_model=SearchMessagesResponse,
    summary="Поиск сообщений",
    description="Полнотекстовый поиск сообщений по содержимому."
)
async def search_messages(
    request: Request,
    query: str = Query(..., min_length=1, max_length=100, description="Поисковый запрос"),
    chat_id: Optional[uuid.UUID] = Query(None, description="Искать в конкретном чате"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=50, description="Количество записей на странице"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Поиск сообщений по тексту"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/online/users",
    response_model=OnlineUsersResponse,
    summary="Онлайн пользователи",
    description="Возвращает список пользователей, находящихся онлайн."
)
async def get_online_users(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка онлайн пользователей"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get(
    "/{chat_id}/match-answers",
    summary="Ответы мэтча в чате",
    description="Получение ответов на вопросы друг друга для чата, созданного из мэтча."
)
async def get_chat_match_answers(
    chat_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Ответы на вопросы в чате"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового чата",
    description="""
    Создает новый чат между пользователями.

    **Личный чат (type=direct):**
    - Требуется ровно один participant_id
    - Название и аватарка генерируются автоматически из профиля собеседника
    - Если чат уже существует, возвращается существующий

    **Групповой чат (type=group):**
    - Требуется минимум один participant_id
    - Название, описание и аватарка задаются создателем
    """
)
async def create_chat(
    chat_data: ChatCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Создание нового чата с автоматической генерацией названия для личных чатов"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/",
    response_model=ChatListResponse,
    summary="Получение списка чатов",
    description="""
    Возвращает список чатов текущего пользователя с персонализированными названиями.

    Для личных чатов название и аватарка будут соответствовать собеседнику.
    """
)
async def list_chats(
    request: Request,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(50, ge=1, le=100, description="Количество записей на странице"),
    chat_type: Optional[str] = Query(None, description="Фильтр по типу чата (direct/group)"),
    status: Optional[str] = Query(None, description="Фильтр по статусу чата (active/archived/blocked)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка чатов пользователя с персонализированными названиями"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Получение информации о чате",
    description="Возвращает детальную информацию о чате с персонализированным названием для текущего пользователя."
)
async def get_chat(
    chat_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение информации о чате"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.put(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Обновление информации о чате",
    description="""
    Обновляет информацию о групповом чате.

    **Важно:** Личные чаты (type=direct) нельзя редактировать.
    """
)
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление информации о групповом чате"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление чата",
    description="Полное удаление чата. Для групповых чатов требуются права администратора."
)
async def delete_chat(
    chat_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправка сообщения",
    description="Отправляет сообщение в чат. Отображаемое имя отправителя берется из profile-service."
)
async def send_message(
    chat_id: uuid.UUID,
    message_data: MessageCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Отправка сообщения в чат"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.get(
    "/{chat_id}/messages",
    response_model=MessageListResponse,
    summary="Получение сообщений",
    description="""
    Возвращает список сообщений чата с отображаемыми именами отправителей.

    Каждое сообщение содержит информацию о прочтении:
    - read_by: список пользователей, прочитавших сообщение
    - read_count: количество прочитавших
    - is_read_by_me: прочитал ли текущий пользователь
    """
)
async def get_messages(
    request: Request,
    chat_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(50, ge=1, le=100, description="Количество записей на странице"),
    before: Optional[str] = Query(None, description="Получить сообщения до этой временной метки (ISO 8601)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение сообщений из чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# === ОБНОВЛЕННЫЙ ЭНДПОИНТ: отметка сообщений как прочитанных ===
@router.post(
    "/{chat_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Отметка сообщений как прочитанных",
    description="""
    Отмечает указанные сообщения как прочитанные для текущего пользователя.

    Отправляет WebSocket уведомления другим участникам чата.
    Максимум 100 сообщений за запрос.
    """
)
async def mark_messages_as_read(
    chat_id: uuid.UUID,
    message_ids: MessageIdsRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Отметка сообщений как прочитанных"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# === НОВЫЙ ЭНДПОИНТ: массовая отметка сообщений как прочитанных ===
@router.post(
    "/{chat_id}/read/bulk",
    status_code=status.HTTP_200_OK,
    summary="Массовая отметка сообщений как прочитанных",
    description="""
    Оптимизированная версия для отметки большого количества сообщений как прочитанных.

    Отправляет одно массовое WebSocket уведомление вместо множества отдельных.
    Максимум 500 сообщений за запрос.
    """
)
async def mark_messages_as_read_bulk(
    chat_id: uuid.UUID,
    message_ids: BulkMessageIdsRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Массовая отметка сообщений как прочитанных"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# === НОВЫЙ ЭНДПОИНТ: получение статуса прочтения сообщения ===
@router.get(
    "/messages/{message_id}/read-status",
    response_model=MessageReadStatusResponse,
    summary="Статус прочтения сообщения",
    description="""
    Возвращает информацию о том, кто прочитал указанное сообщение.

    Включает:
    - Список пользователей, прочитавших сообщение
    - Время прочтения для каждого
    - Общее количество прочитавших
    """
)
async def get_message_read_status(
    message_id: uuid.UUID,
    request: Request,
    chat_id: uuid.UUID = Query(..., description="ID чата, содержащего сообщение"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение информации о прочитавших сообщение"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление сообщения",
    description="Удаляет сообщение. Можно удалить свое сообщение или любое при наличии прав администратора."
)
async def delete_message(
    message_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление сообщения"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.put(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Редактирование сообщения",
    description="""
    Редактирование сообщения.

    - Только отправитель может редактировать сообщение
    - Редактирование возможно в течение 24 часов после отправки
    - Всем участникам чата отправляется WebSocket уведомление message_updated
    - В ответе будет is_edited=true
    """
)
async def update_message(
    message_id: uuid.UUID,
    message_data: MessageUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Редактирование сообщения"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.post(
    "/{chat_id}/participants/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Добавление участника",
    description="Добавляет нового участника в групповой чат. Требуются права администратора."
)
async def add_participant(
    chat_id: uuid.UUID,
    user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Добавление участника в групповой чат"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@router.delete(
    "/{chat_id}/participants/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Удаление участника",
    description="Удаляет участника из группового чата. Можно удалить себя или другого при наличии прав администратора."
)
async def remove_participant(
    chat_id: uuid.UUID,
    user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление участника из группового чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# === ДОПОЛНИТЕЛЬНЫЙ ЭНДПОИНТ: проверка онлайн статуса пользователя ===
@router.get(
    "/online/users/{keycloak_id}",
    summary="Проверка онлайн статуса",
    description="Проверяет, находится ли указанный пользователь онлайн."
)
async def check_user_online(
    keycloak_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Проверка онлайн статуса конкретного пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# === ОПЦИОНАЛЬНО: эндпоинт для получения непрочитанных сообщений ===
@router.get(
    "/{chat_id}/unread/count",
    summary="Количество непрочитанных",
    description="Возвращает количество непрочитанных сообщений в чате для текущего пользователя."
)
async def get_unread_count(
    chat_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение количества непрочитанных сообщений"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
