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
    """WebSocket endpoint для реального времени с поддержкой display_name и heartbeat"""
    if not user_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    keycloak_id = user_data.get("keycloak_id")
    display_name = user_data.get("display_name", keycloak_id[:8])
    
    if not keycloak_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Подключаем пользователя
    connection_id = await websocket_manager.connect(websocket, keycloak_id)
    
    try:
        # Отправляем приветственное сообщение
        welcome_message = WebSocketMessage(
            type="connection_established",
            message={
                "connection_id": connection_id,
                "user_id": keycloak_id,
                "display_name": display_name
            },
            timestamp=datetime.utcnow()
        )
        await websocket.send_json(welcome_message.model_dump(mode='json'))
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение с таймаутом
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=settings.websocket.timeout
                )
                
                # Обрабатываем сообщение
                await _handle_websocket_message(data, keycloak_id, display_name, connection_id)
                
            except asyncio.TimeoutError:
                # Проверка keep-alive - отправляем ping
                ping_message = WebSocketMessage(
                    type="ping",
                    timestamp=datetime.utcnow()
                )
                try:
                    await websocket.send_json(ping_message.model_dump(mode='json'))
                except Exception:
                    # Клиент не отвечает, разрываем соединение
                    logger.warning(f"Client {keycloak_id} not responding to ping")
                    break
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {keycloak_id}")
                error_message = WebSocketMessage(
                    type="error",
                    message={"error": "Invalid JSON format"},
                    timestamp=datetime.utcnow()
                )
                await websocket.send_json(error_message.model_dump(mode='json'))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {keycloak_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {keycloak_id}: {e}", exc_info=True)
    finally:
        # Отключаем пользователя
        await websocket_manager.disconnect(connection_id, reason="disconnect")

async def _handle_websocket_message(data: dict, keycloak_id: str, display_name: str, connection_id: str):
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
                response.model_dump(mode='json'),
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
                chat_id, keycloak_id, is_typing
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
                
    elif message_type == "message_update":
        # Редактирование сообщения через WebSocket
        chat_id = data.get("chat_id")
        message_id = data.get("message_id")
        new_content = data.get("content")
        
        if chat_id and message_id and new_content:
            try:
                from app.schemas.chat import MessageUpdate
                from app.services.chat_service import ChatService
                from app.database.postgres.session import async_session_factory
                
                async with async_session_factory() as session:
                    service = ChatService(session)
                    message_uuid = uuid.UUID(message_id)
                    update_data = MessageUpdate(content=new_content)
                    
                    await service.update_message(
                        message_id=message_uuid,
                        message_data=update_data,
                        sender_keycloak_id=keycloak_id
                    )
                    # Успешное обновление отправляется через broadcast внутри update_message
            except ValueError:
                logger.warning(f"Invalid message ID for update: {message_id}")
            except Exception as e:
                logger.error(f"Error updating message via WebSocket: {e}")
                error_message = WebSocketMessage(
                    type="error",
                    message={"error": f"Failed to update message: {str(e)}"},
                    timestamp=datetime.utcnow()
                )
                await websocket_manager.send_personal_message(
                    error_message.model_dump(mode='json'),
                    keycloak_id
                )
    
    elif message_type == "ping":
        # Heartbeat от клиента - продлеваем статус
        await websocket_manager.handle_heartbeat(keycloak_id, connection_id)
        
        # Отвечаем pong
        pong_message = WebSocketMessage(
            type="pong",
            timestamp=datetime.utcnow()
        )
        await websocket_manager.send_personal_message(
            pong_message.model_dump(mode='json'),
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
            error_message.model_dump(mode='json'),
            keycloak_id
        )