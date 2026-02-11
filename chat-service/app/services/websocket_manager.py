import asyncio
import json
import uuid
from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
import logging

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import WebSocketException, RateLimitException
from app.schemas.chat import WebSocketMessage, TypingIndicator, ReadReceipt
from app.services.profile_service_client import get_profile_service_client

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # keycloak_id -> connection_ids
        self.connection_users: Dict[str, str] = {}  # connection_id -> keycloak_id
        self.chat_subscriptions: Dict[str, Set[str]] = {}  # chat_id -> connection_ids
        self._lock = asyncio.Lock()
        self.redis_client: Optional[redis.Redis] = None
        self._redis_connected = False
        self.profile_client = get_profile_service_client()
    
    async def _get_redis(self):
        """Ленивая инициализация Redis"""
        if not self._redis_connected:
            try:
                self.redis_client = redis.from_url(
                    settings.redis.url,
                    decode_responses=True
                )
                await self.redis_client.ping()
                self._redis_connected = True
                logger.info("Redis client initialized for WebSocket manager")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        
        return self.redis_client
    
    async def check_rate_limit(self, keycloak_id: str) -> bool:
        """Проверка rate limiting для сообщений"""
        redis_client = await self._get_redis()
        if not redis_client:
            return True  # Если Redis недоступен, пропускаем rate limiting
        
        key = f"ws_rate_limit:{keycloak_id}"
        current = await redis_client.get(key)
        
        if current is None:
            await redis_client.setex(
                key,
                settings.websocket.message_rate_window,
                1
            )
            return True
        
        current_count = int(current)
        if current_count >= settings.websocket.message_rate_limit:
            return False
        
        await redis_client.incr(key)
        return True
    
    async def connect(self, websocket: WebSocket, keycloak_id: str) -> str:
        """Подключение нового WebSocket клиента"""
        connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        async with self._lock:
            self.active_connections[connection_id] = websocket
            self.connection_users[connection_id] = keycloak_id
            
            if keycloak_id not in self.user_connections:
                self.user_connections[keycloak_id] = set()
            self.user_connections[keycloak_id].add(connection_id)
            
            # Записываем онлайн статус в Redis
            redis_client = await self._get_redis()
            if redis_client:
                await redis_client.setex(
                    f"user_online:{keycloak_id}",
                    settings.websocket.timeout + 30,
                    "online"
                )
        
        logger.info(f"User {keycloak_id} connected with connection {connection_id[:8]}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Отключение WebSocket клиента"""
        async with self._lock:
            if connection_id in self.connection_users:
                keycloak_id = self.connection_users[connection_id]
                
                # Удаляем из активных соединений
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
                
                # Удаляем из связей пользователь-соединение
                if keycloak_id in self.user_connections:
                    self.user_connections[keycloak_id].discard(connection_id)
                    if not self.user_connections[keycloak_id]:
                        del self.user_connections[keycloak_id]
                
                # Удаляем из отслеживания соединений
                del self.connection_users[connection_id]
                
                # Удаляем из подписок на чаты
                for chat_id in list(self.chat_subscriptions.keys()):
                    self.chat_subscriptions[chat_id].discard(connection_id)
                    if not self.chat_subscriptions[chat_id]:
                        del self.chat_subscriptions[chat_id]
                
                logger.info(f"User {keycloak_id} disconnected from {connection_id[:8]}")
                
                # Обновляем онлайн статус
                redis_client = await self._get_redis()
                if redis_client and keycloak_id not in self.user_connections:
                    await redis_client.delete(f"user_online:{keycloak_id}")
    
    async def subscribe_to_chat(self, connection_id: str, chat_id: str):
        """Подписка на обновления чата"""
        async with self._lock:
            if chat_id not in self.chat_subscriptions:
                self.chat_subscriptions[chat_id] = set()
            self.chat_subscriptions[chat_id].add(connection_id)
    
    async def unsubscribe_from_chat(self, connection_id: str, chat_id: str):
        """Отписка от обновлений чата"""
        async with self._lock:
            if chat_id in self.chat_subscriptions:
                self.chat_subscriptions[chat_id].discard(connection_id)
                if not self.chat_subscriptions[chat_id]:
                    del self.chat_subscriptions[chat_id]
    
    async def send_personal_message(self, message: dict, keycloak_id: str):
        """Отправка сообщения конкретному пользователю"""
        async with self._lock:
            if keycloak_id in self.user_connections:
                for connection_id in list(self.user_connections[keycloak_id]):
                    if connection_id in self.active_connections:
                        try:
                            await self.active_connections[connection_id].send_json(message)
                        except Exception as e:
                            logger.error(f"Failed to send message to {connection_id[:8]}: {e}")
                            # Удаляем нерабочее соединение
                            await self.disconnect(connection_id)
    
    async def broadcast_to_chat(self, message: dict, chat_id: str, exclude_user: Optional[str] = None):
        """Рассылка сообщения всем участникам чата"""
        async with self._lock:
            if chat_id in self.chat_subscriptions:
                for connection_id in list(self.chat_subscriptions[chat_id]):
                    if connection_id in self.connection_users:
                        user_id = self.connection_users[connection_id]
                        if user_id != exclude_user and connection_id in self.active_connections:
                            try:
                                await self.active_connections[connection_id].send_json(message)
                            except Exception as e:
                                logger.error(f"Failed to broadcast to {connection_id[:8]}: {e}")
                                await self.disconnect(connection_id)
    
    async def send_typing_indicator(self, chat_id: str, user_id: str, is_typing: bool):
        """Отправка индикатора набора текста с display_name"""
        # Получаем display_name из profile-service
        display_name = await self.profile_client.get_display_name(user_id)
        
        indicator = TypingIndicator(
            chat_id=chat_id,
            user_id=user_id,
            display_name=display_name,
            is_typing=is_typing
        )
        
        message = WebSocketMessage(
            type="typing",
            chat_id=chat_id,
            message=indicator.model_dump(mode='json'),
            sender_id=user_id,
            timestamp=datetime.utcnow()
        )
        
        await self.broadcast_to_chat(
            message.model_dump(mode='json'),
            str(chat_id),
            exclude_user=user_id
        )
    
    async def send_read_receipt(self, chat_id: str, user_id: str, message_id: uuid.UUID):
        """Отправка подтверждения прочтения"""
        receipt = ReadReceipt(
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            read_at=datetime.utcnow()
        )
        
        message = WebSocketMessage(
            type="read_receipt",
            chat_id=chat_id,
            message=receipt.model_dump(mode='json'),
            sender_id=user_id,
            timestamp=datetime.utcnow()
        )
        
        await self.broadcast_to_chat(
            message.model_dump(mode='json'),
            str(chat_id),
            exclude_user=user_id
        )
    
    async def is_user_online(self, keycloak_id: str) -> bool:
        """Проверка онлайн статуса пользователя"""
        redis_client = await self._get_redis()
        if redis_client:
            online = await redis_client.get(f"user_online:{keycloak_id}")
            return online is not None
        
        # Fallback: проверка активных соединений
        async with self._lock:
            return keycloak_id in self.user_connections
    
    async def get_online_users(self) -> List[str]:
        """Получение списка онлайн пользователей"""
        async with self._lock:
            return list(self.user_connections.keys())
    
    def get_connection_count(self) -> int:
        """Получение количества активных соединений"""
        return len(self.active_connections)
    
    async def disconnect_all(self):
        """Отключение всех соединений"""
        async with self._lock:
            for connection_id in list(self.active_connections.keys()):
                try:
                    await self.active_connections[connection_id].close()
                except Exception as e:
                    logger.error(f"Error closing connection {connection_id[:8]}: {e}")
            
            self.active_connections.clear()
            self.user_connections.clear()
            self.connection_users.clear()
            self.chat_subscriptions.clear()
            
            logger.info("All WebSocket connections disconnected")

# Глобальный экземпляр менеджера
websocket_manager = ConnectionManager()