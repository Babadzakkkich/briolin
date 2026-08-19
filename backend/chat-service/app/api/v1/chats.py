from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, status
import uuid

from app.services.chat_service import ChatService
from app.dependencies import get_chat_service, get_current_active_user, require_role
from app.schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatListResponse,
    MessageCreate, MessageResponse, MessageListResponse,
    MessageIdsRequest, MessageUpdate, OnlineUsersResponse, 
    SearchMessagesResponse, MessageReadStatusResponse
)
from app.services.websocket_manager import websocket_manager
from app.services.matching_service_client import get_matching_client
from shared.schemas.shared import UserRole
from app.core.logger import logger

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/search/messages", response_model=SearchMessagesResponse)
async def search_messages(
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    chat_id: Optional[uuid.UUID] = Query(None, description="Search in specific chat"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(20, ge=1, le=50, description="Limit records"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Поиск сообщений по тексту"""
    messages = await service.search_messages(
        current_user["keycloak_id"],
        query,
        chat_id,
        skip,
        limit
    )
    return SearchMessagesResponse(
        messages=messages,
        total=len(messages),
        query=query
    )


@router.get(
    "/{chat_id}/match-answers",
    summary="Ответы на вопросы в матче",
    description="""
    Возвращает ответы на вопросы друг друга, если чат создан из матча.
    
    Включает:
    - Мои ответы на его вопросы
    - Мои вопросы
    - Его ответы на мои вопросы
    - Его вопросы
    """
)
async def get_chat_match_answers(
    chat_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение ответов на вопросы для чата"""
    answers = await service.get_chat_match_answers(
        chat_id=chat_id,
        keycloak_id=current_user["keycloak_id"]
    )
    
    if not answers:
        raise HTTPException(
            status_code=404,
            detail="Этот чат не связан с матчем или ответы не найдены"
        )
    
    return answers

@router.get("/online/users", response_model=OnlineUsersResponse)
async def get_online_users(
    current_user: dict = Depends(get_current_active_user)
):
    """Получение списка онлайн пользователей"""
    online_users = await websocket_manager.get_online_users()
    return {
        "online_users": online_users,
        "count": len(online_users)
    }


@router.get("/online/users/count")
async def get_online_users_count(
    current_user: dict = Depends(get_current_active_user)
):
    """Получение количества онлайн пользователей"""
    count = websocket_manager.get_online_users_count()
    return {"count": count}


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Создание нового чата.
    
    Для личного чата (type=direct):
    - Название и аватарка генерируются автоматически на основе профиля собеседника
    - Должен быть указан ровно один participant_id
    
    Для группового чата (type=group):
    - Название и аватарка задаются создателем
    - Можно указать несколько участников
    """
    return await service.create_chat(
        chat_data,
        current_user["keycloak_id"],
        current_user.get("username", current_user["keycloak_id"])
    )


@router.get("/", response_model=ChatListResponse)
async def list_chats(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    chat_type: Optional[str] = Query(None, description="Filter by chat type (direct/group)"),
    status: Optional[str] = Query(None, description="Filter by chat status"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение списка чатов пользователя с персонализированными названиями"""
    from app.database.postgres.models import ChatType, ChatStatus
    
    type_enum = None
    if chat_type:
        try:
            type_enum = ChatType(chat_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid chat_type: {chat_type}")
    
    status_enum = None
    if status:
        try:
            status_enum = ChatStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    chats, total = await service.list_chats(
        current_user["keycloak_id"],
        skip=skip,
        limit=limit,
        chat_type=type_enum,
        status=status_enum
    )
    
    return ChatListResponse(
        chats=chats,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение информации о чате с персонализированным названием"""
    return await service.get_chat(chat_id, current_user["keycloak_id"])


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatUpdate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Обновление информации о чате (только для групповых чатов)"""
    return await service.update_chat(chat_id, chat_data, current_user["keycloak_id"])


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Удаление чата"""
    await service.delete_chat(chat_id, current_user["keycloak_id"])
    return {"message": "Chat deleted successfully"}


@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: uuid.UUID,
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Отправка сообщения в чат (отображаемое имя берется из profile-service)"""
    return await service.send_message(
        chat_id=chat_id,
        message_data=message_data,
        sender_keycloak_id=current_user["keycloak_id"],
        sender_username=current_user.get("username", current_user["keycloak_id"])
    )


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def get_messages(
    chat_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    before: Optional[str] = Query(None, description="Get messages before this timestamp (ISO format)"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение сообщений из чата с информацией о прочтении"""
    before_date = None
    if before:
        try:
            before_date = datetime.fromisoformat(before.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid before timestamp format")
    
    messages, total = await service.get_messages(
        chat_id,
        current_user["keycloak_id"],
        skip=skip,
        limit=limit,
        before=before_date
    )
    
    return MessageListResponse(
        messages=messages,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


# === ОБНОВЛЕННЫЙ ЭНДПОИНТ: отметка сообщений как прочитанных ===
@router.post("/{chat_id}/read")
async def mark_messages_as_read(
    chat_id: uuid.UUID,
    message_ids: MessageIdsRequest,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Отметка сообщений как прочитанных.
    
    Отмечает указанные сообщения как прочитанные для текущего пользователя.
    Отправляет WebSocket уведомления другим участникам чата.
    """
    await service.mark_messages_as_read(
        chat_id,
        current_user["keycloak_id"],
        message_ids.message_ids,
        notify=True
    )
    return {"message": "Messages marked as read"}


# === НОВЫЙ ЭНДПОИНТ: массовая отметка сообщений как прочитанных ===
@router.post("/{chat_id}/read/bulk")
async def mark_messages_as_read_bulk(
    chat_id: uuid.UUID,
    message_ids: MessageIdsRequest,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Массовая отметка сообщений как прочитанных.
    
    Оптимизированная версия для отметки большого количества сообщений.
    Отправляет одно массовое WebSocket уведомление вместо множества отдельных.
    """
    await service.mark_messages_as_read(
        chat_id,
        current_user["keycloak_id"],
        message_ids.message_ids,
        notify=True
    )
    return {"message": f"{len(message_ids.message_ids)} messages marked as read"}


# === НОВЫЙ ЭНДПОИНТ: получение статуса прочтения сообщения ===
@router.get("/messages/{message_id}/read-status", response_model=MessageReadStatusResponse)
async def get_message_read_status(
    message_id: uuid.UUID,
    chat_id: uuid.UUID = Query(..., description="ID чата, содержащего сообщение"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Получение информации о том, кто прочитал сообщение.
    
    Возвращает список пользователей, которые прочитали указанное сообщение,
    с временем прочтения.
    """
    return await service.get_message_read_status(
        chat_id=chat_id,
        message_id=message_id,
        keycloak_id=current_user["keycloak_id"]
    )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Удаление сообщения"""
    await service.delete_message(message_id, current_user["keycloak_id"])
    return {"message": "Message deleted successfully"}


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: uuid.UUID,
    message_data: MessageUpdate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Редактирование сообщения (только отправитель, в течение 24 часов)"""
    return await service.update_message(
        message_id=message_id,
        message_data=message_data,
        sender_keycloak_id=current_user["keycloak_id"]
    )


@router.post("/{chat_id}/participants/{user_id}")
async def add_participant(
    chat_id: uuid.UUID,
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Добавление участника в групповой чат"""
    await service.add_participant(
        chat_id,
        current_user["keycloak_id"],
        user_id
    )
    return {"message": "Participant added successfully"}


@router.delete("/{chat_id}/participants/{user_id}")
async def remove_participant(
    chat_id: uuid.UUID,
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Удаление участника из группового чата"""
    await service.remove_participant(chat_id, current_user["keycloak_id"], user_id)
    return {"message": "Participant removed successfully"}


@router.get("/online/users/{keycloak_id}")
async def check_user_online(
    keycloak_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Проверка онлайн статуса конкретного пользователя"""
    is_online = await websocket_manager.is_user_online(keycloak_id)
    return {
        "keycloak_id": keycloak_id,
        "online": is_online
    }