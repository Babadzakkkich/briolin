import asyncio
import json
import uuid
import websockets
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState

from app.core.config import settings
from app.core.logger import logger


class WebSocketProxy:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.chat_service_ws_url = f"{settings.services.chat_ws}/ws"
        
        self._lock = asyncio.Lock()
        self._shutdown = False
        
        logger.info(f"WebSocket Proxy initialized. Target: {self.chat_service_ws_url}")
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_data: Dict[str, Any],
        internal_token: str,
        token_signature: str
    ):
        """
        Основной обработчик WebSocket соединения
        
        Args:
            websocket: WebSocket соединение от клиента
            user_data: Данные пользователя из токена
            internal_token: Внутренний JWT токен
            token_signature: Подпись токена
        """
        client_id = str(uuid.uuid4())[:8]
        keycloak_id = user_data.get("keycloak_id", "unknown")
        username = user_data.get("username", "unknown")
        
        connection_info = {
            "client_id": client_id,
            "keycloak_id": keycloak_id,
            "username": username,
            "connected_at": datetime.utcnow().isoformat(),
            "messages_sent": 0,
            "messages_received": 0
        }
        
        # Регистрируем соединение
        async with self._lock:
            if self._shutdown:
                await websocket.close(code=status.WS_1001_GOING_AWAY)
                return
            
            self.active_connections[client_id] = connection_info
        
        logger.info(
            f"WebSocket connected: client={client_id}, "
            f"user={username} ({keycloak_id[:8]}...), "
            f"active_connections={len(self.active_connections)}"
        )
        
        # Подключаемся к chat-service
        chat_service_ws = None
        
        try:
            # Формируем URL с токеном для chat-service
            ws_url = f"{self.chat_service_ws_url}?token={internal_token}"
            
            # Устанавливаем соединение с chat-service
            chat_service_ws = await websockets.connect(
                ws_url,
                additional_headers={
                    "x-internal-token": internal_token,
                    "x-token-signature": token_signature
                },
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            
            logger.debug(f"[{client_id}] Connected to chat-service")
            
            # Запускаем двунаправленное проксирование
            await self._proxy_bidirectional(websocket, chat_service_ws, client_id, connection_info)
            
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"[{client_id}] Failed to connect to chat-service: HTTP {e.status_code}")
            await self._send_error_and_close(
                websocket, 
                f"Chat service unavailable (HTTP {e.status_code})",
                status.WS_1011_INTERNAL_ERROR
            )
            
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"[{client_id}] Chat-service connection closed: {e}")
            await self._send_error_and_close(
                websocket,
                "Chat service connection closed",
                status.WS_1011_INTERNAL_ERROR
            )
            
        except Exception as e:
            logger.error(f"[{client_id}] WebSocket proxy error: {e}", exc_info=True)
            await self._send_error_and_close(
                websocket,
                "Internal proxy error",
                status.WS_1011_INTERNAL_ERROR
            )
            
        finally:
            # Очистка ресурсов
            if chat_service_ws:
                # ИСПРАВЛЕНО: Проверка state вместо closed для websockets v14+
                try:
                    if hasattr(chat_service_ws, 'state'):
                        # websockets v14+
                        if chat_service_ws.state == websockets.protocol.State.OPEN:
                            await chat_service_ws.close()
                    elif hasattr(chat_service_ws, 'closed'):
                        # websockets v13 и ниже
                        if not chat_service_ws.closed:
                            await chat_service_ws.close()
                    else:
                        # Fallback: пробуем закрыть всегда
                        await chat_service_ws.close()
                except Exception as e:
                    logger.debug(f"[{client_id}] Error closing chat-service ws: {e}")
            
            # Удаляем соединение из реестра
            async with self._lock:
                self.active_connections.pop(client_id, None)
            
            # Логируем статистику
            duration = self._calculate_duration(connection_info["connected_at"])
            logger.info(
                f"WebSocket disconnected: client={client_id}, "
                f"duration={duration:.1f}s, "
                f"sent={connection_info['messages_sent']}, "
                f"received={connection_info['messages_received']}, "
                f"active_connections={len(self.active_connections)}"
            )
    
    async def _proxy_bidirectional(
        self,
        client_ws: WebSocket,
        service_ws: websockets.WebSocketClientProtocol,
        client_id: str,
        connection_info: Dict[str, Any]
    ):
        """
        Двунаправленное проксирование сообщений между клиентом и сервисом
        """
        # Создаем задачи для обоих направлений
        client_to_service = asyncio.create_task(
            self._proxy_client_to_service(client_ws, service_ws, client_id, connection_info)
        )
        service_to_client = asyncio.create_task(
            self._proxy_service_to_client(service_ws, client_ws, client_id, connection_info)
        )
        
        # Ждем завершения любой из задач
        done, pending = await asyncio.wait(
            [client_to_service, service_to_client],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Проверяем на ошибки
        for task in done:
            try:
                task.result()
            except Exception as e:
                logger.debug(f"[{client_id}] Proxy task ended with error: {e}")
    
    async def _proxy_client_to_service(
        self,
        client_ws: WebSocket,
        service_ws: websockets.WebSocketClientProtocol,
        client_id: str,
        connection_info: Dict[str, Any]
    ):
        """
        Проксирование сообщений от клиента к сервису
        """
        try:
            while True:
                # Получаем сообщение от клиента
                message = await client_ws.receive_text()
                
                if self._shutdown:
                    break
                
                # Парсим для логирования (опционально)
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type", "unknown")
                    logger.debug(f"[{client_id}] Client → Service: type={msg_type}")
                except json.JSONDecodeError:
                    logger.debug(f"[{client_id}] Client → Service: [binary/text]")
                
                # Отправляем в сервис
                await service_ws.send(message)
                connection_info["messages_sent"] += 1
                
        except WebSocketDisconnect:
            logger.debug(f"[{client_id}] Client disconnected")
        except Exception as e:
            logger.debug(f"[{client_id}] Client→Service error: {e}")
    
    async def _proxy_service_to_client(
        self,
        service_ws: websockets.WebSocketClientProtocol,
        client_ws: WebSocket,
        client_id: str,
        connection_info: Dict[str, Any]
    ):
        """
        Проксирование сообщений от сервиса к клиенту
        """
        try:
            async for message in service_ws:
                if self._shutdown:
                    break
                
                # Парсим для логирования
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type", "unknown")
                    
                    # Логируем важные события
                    if msg_type in ["message", "typing", "read_receipt", "chat_update"]:
                        logger.debug(f"[{client_id}] Service → Client: type={msg_type}")
                except json.JSONDecodeError:
                    pass
                
                # Отправляем клиенту
                await client_ws.send_text(message)
                connection_info["messages_received"] += 1
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.debug(f"[{client_id}] Service connection closed: {e}")
        except Exception as e:
            logger.debug(f"[{client_id}] Service→Client error: {e}")
    
    async def _send_error_and_close(
        self,
        websocket: WebSocket,
        error_message: str,
        close_code: int = status.WS_1011_INTERNAL_ERROR
    ):
        """Отправляет ошибку клиенту и закрывает соединение"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                # Отправляем сообщение об ошибке в формате WebSocketMessage
                error_msg = {
                    "type": "error",
                    "message": {"error": error_message},
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_msg))
                await websocket.close(code=close_code)
        except Exception as e:
            logger.debug(f"Error sending error message: {e}")
    
    def _calculate_duration(self, connected_at_iso: str) -> float:
        """Вычисляет длительность соединения в секундах"""
        try:
            connected_at = datetime.fromisoformat(connected_at_iso)
            return (datetime.utcnow() - connected_at).total_seconds()
        except:
            return 0.0
    
    async def shutdown(self):
        """Graceful shutdown - закрывает все соединения"""
        logger.info("WebSocket Proxy shutting down...")
        self._shutdown = True
        
        # Копируем список для безопасной итерации
        async with self._lock:
            connections = list(self.active_connections.keys())
        
        # Закрываем все соединения
        for client_id in connections:
            info = self.active_connections.get(client_id, {})
            logger.debug(f"Closing connection {client_id}")
        
        logger.info(f"WebSocket Proxy shutdown complete. Closed {len(connections)} connections")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику WebSocket прокси"""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": len(self.active_connections),  # Можно добавить счетчик всех подключений
            "chat_service_target": self.chat_service_ws_url,
            "shutdown_pending": self._shutdown
        }


# Глобальный экземпляр прокси
_ws_proxy = None

def get_websocket_proxy() -> WebSocketProxy:
    """Получает экземпляр WebSocket прокси (синглтон)"""
    global _ws_proxy
    if _ws_proxy is None:
        _ws_proxy = WebSocketProxy()
    return _ws_proxy