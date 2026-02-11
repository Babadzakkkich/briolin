from typing import Optional, List
from fastapi import APIRouter, Request, Depends, Response, Query, Body, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

from app.services.http_client import http_client
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    MessageIdsRequest,
    SearchMessagesResponse,
    OnlineUsersResponse,
    WebSocketMessage,
    TypingIndicator,
    ReadReceipt
)

router = APIRouter(prefix="/chats", tags=["Chats"])
security = HTTPBearer(auto_error=False)

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
    description="Возвращает список сообщений чата с отображаемыми именами отправителей."
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

@router.post(
    "/{chat_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Отметка сообщений как прочитанных",
    description="Отмечает указанные сообщения как прочитанные и отправляет уведомления через WebSocket."
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