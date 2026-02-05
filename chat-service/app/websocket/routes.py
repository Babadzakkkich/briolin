import asyncio
import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.websocket_manager import websocket_manager
from app.dependencies import get_current_user_ws
from app.core.logger import logger
from app.schemas.chat import WebSocketMessage, TypingIndicator

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    user_data: Optional[dict] = Depends(get_current_user_ws)
):
    """WebSocket endpoint для реального времени"""
    if not user_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    keycloak_id = user_data.get("keycloak_id")
    username = user_data.get("username")
    
    if not keycloak_id or not username:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Подключаем пользователя
    connection_id = await websocket_manager.connect(websocket, keycloak_id)
    
    try:
        # Отправляем приветственное сообщение
        welcome_message = WebSocketMessage(
            type="connection_established",
            message={"connection_id": connection_id, "user_id": keycloak_id},
            timestamp=datetime.utcnow()
        )
        await websocket.send_json(welcome_message.model_dump())
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение с таймаутом
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=settings.websocket.timeout
                )
                
                # Обрабатываем сообщение
                await _handle_websocket_message(data, keycloak_id, username, connection_id)
                
            except asyncio.TimeoutError:
                # Проверка keep-alive
                ping_message = WebSocketMessage(
                    type="ping",
                    timestamp=datetime.utcnow()
                )
                await websocket.send_json(ping_message.model_dump())
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {keycloak_id}")
                error_message = WebSocketMessage(
                    type="error",
                    message={"error": "Invalid JSON format"},
                    timestamp=datetime.utcnow()
                )
                await websocket.send_json(error_message.model_dump())
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {keycloak_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {keycloak_id}: {e}", exc_info=True)
    finally:
        # Отключаем пользователя
        await websocket_manager.disconnect(connection_id)

async def _handle_websocket_message(data: dict, keycloak_id: str, username: str, connection_id: str):
    """Обработка входящих WebSocket сообщений"""
    message_type = data.get("type")
    
    if message_type == "subscribe":
        # Подписка на чат
        chat_id = data.get("chat_id")
        if chat_id:
            await websocket_manager.subscribe_to_chat(connection_id, chat_id)
            
            # Отправляем подтверждение
            response = WebSocketMessage(
                type="subscribed",
                chat_id=chat_id,
                message={"chat_id": chat_id, "status": "subscribed"},
                timestamp=datetime.utcnow()
            )
            await websocket_manager.send_personal_message(
                response.model_dump(),
                keycloak_id
            )
    
    elif message_type == "unsubscribe":
        # Отписка от чата
        chat_id = data.get("chat_id")
        if chat_id:
            await websocket_manager.unsubscribe_from_chat(connection_id, chat_id)
    
    elif message_type == "typing":
        # Индикатор набора текста
        chat_id = data.get("chat_id")
        is_typing = data.get("is_typing", False)
        
        if chat_id:
            await websocket_manager.send_typing_indicator(
                chat_id, keycloak_id, username, is_typing
            )
    
    elif message_type == "read_receipt":
        # Подтверждение прочтения
        chat_id = data.get("chat_id")
        message_id = data.get("message_id")
        
        if chat_id and message_id:
            try:
                message_uuid = uuid.UUID(message_id)
                await websocket_manager.send_read_receipt(
                    chat_id, keycloak_id, message_uuid
                )
            except ValueError:
                logger.warning(f"Invalid message ID: {message_id}")
    
    elif message_type == "ping":
        # Ответ на ping
        pong_message = WebSocketMessage(
            type="pong",
            timestamp=datetime.utcnow()
        )
        await websocket_manager.send_personal_message(
            pong_message.model_dump(),
            keycloak_id
        )
    
    else:
        logger.warning(f"Unknown message type from {keycloak_id}: {message_type}")
        error_message = WebSocketMessage(
            type="error",
            message={"error": f"Unknown message type: {message_type}"},
            timestamp=datetime.utcnow()
        )
        await websocket_manager.send_personal_message(
            error_message.model_dump(),
            keycloak_id
        )