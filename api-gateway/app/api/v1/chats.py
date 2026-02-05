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
    OnlineUsersResponse
)

router = APIRouter(prefix="/chats", tags=["Chats"])
security = HTTPBearer(auto_error=False)

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Создание нового чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/", response_model=ChatListResponse)
async def list_chats(
    request: Request,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    chat_type: Optional[str] = Query(None, description="Filter by chat type"),
    status: Optional[str] = Query(None, description="Filter by chat status"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка чатов пользователя"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/{chat_id}", response_model=ChatResponse)
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

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновление информации о чате"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
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

@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def get_messages(
    request: Request,
    chat_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(50, ge=1, le=100, description="Limit records"),
    before: Optional[str] = Query(None, description="Get messages before this timestamp"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение сообщений из чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.post("/{chat_id}/read", status_code=status.HTTP_200_OK)
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

@router.post("/{chat_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def add_participant(
    chat_id: uuid.UUID,
    user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Добавление участника в чат"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.delete("/{chat_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def remove_participant(
    chat_id: uuid.UUID,
    user_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление участника из чата"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/search/messages", response_model=SearchMessagesResponse)
async def search_messages(
    request: Request,
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    chat_id: Optional[uuid.UUID] = Query(None, description="Search in specific chat"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(20, ge=1, le=50, description="Limit records"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Поиск сообщений по тексту"""
    response = await http_client.proxy_request(request)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@router.get("/online/users", response_model=OnlineUsersResponse)
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