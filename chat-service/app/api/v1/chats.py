from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, status
import uuid

from app.services.chat_service import ChatService
from app.dependencies import get_chat_service, get_current_active_user, require_role
from app.schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatListResponse,
    MessageCreate, MessageResponse, MessageListResponse
)
from app.services import websocket_manager
from shared.schemas.shared import UserRole
from app.core.logger import logger

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Создание нового чата"""
    return await service.create_chat(
        chat_data,
        current_user["keycloak_id"],
        current_user["username"]
    )

@router.get("/", response_model=ChatListResponse)
async def list_chats(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    chat_type: Optional[str] = Query(None, description="Filter by chat type"),
    status: Optional[str] = Query(None, description="Filter by chat status"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение списка чатов пользователя"""
    chats, total = await service.list_chats(
        current_user["keycloak_id"],
        skip=skip,
        limit=limit,
        chat_type=chat_type,
        status=status
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
    """Получение информации о чате"""
    return await service.get_chat(chat_id, current_user["keycloak_id"])

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatUpdate,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Обновление информации о чате"""
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
    """Отправка сообщения в чат"""
    # chat_id берется из URL path, а не из тела запроса
    return await service.send_message(
        chat_id=chat_id,  # Явно передаем chat_id из URL
        message_data=message_data,
        sender_keycloak_id=current_user["keycloak_id"],
        sender_username=current_user["username"]
    )

@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def get_messages(
    chat_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    before: Optional[str] = Query(None, description="Get messages before this timestamp"),
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Получение сообщений из чата"""
    before_date = None
    if before:
        try:
            before_date = datetime.fromisoformat(before.replace('Z', '+00:00'))
        except ValueError:
            pass
    
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

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Удаление сообщения"""
    await service.delete_message(message_id, current_user["keycloak_id"])
    return {"message": "Message deleted successfully"}

@router.post("/{chat_id}/read")
async def mark_messages_as_read(
    chat_id: uuid.UUID,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Отметка сообщений как прочитанных"""
    # Парсим body вручную
    body = await request.json()
    message_ids_raw = body.get("message_ids", [])
    
    # Валидируем UUID
    message_ids = []
    for mid in message_ids_raw:
        try:
            message_ids.append(uuid.UUID(mid))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid UUID: {mid}")
    
    await service.mark_messages_as_read(chat_id, current_user["keycloak_id"], message_ids)
    return {"message": "Messages marked as read"}

@router.post("/{chat_id}/participants/{user_id}")
async def add_participant(
    chat_id: uuid.UUID,
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service)
):
    """Добавление участника в чат"""
    # Больше не нужно передавать username — сервис сам получит его из user-service
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
    """Удаление участника из чата"""
    await service.remove_participant(chat_id, current_user["keycloak_id"], user_id)
    return {"message": "Participant removed successfully"}

@router.get("/search/messages")
async def search_messages(
    query: str = Query(..., min_length=1, max_length=100),
    chat_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
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
    return {"messages": messages, "total": len(messages), "query": query}

@router.get("/online/users")
async def get_online_users(
    current_user: dict = Depends(get_current_active_user)
):
    """Получение списка онлайн пользователей"""
    online_users = await websocket_manager.get_online_users()
    return {"online_users": online_users, "count": len(online_users)}