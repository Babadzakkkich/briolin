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
from app.services.event_service import get_event_service

class ConnectionManager:
    """Менеджер WebSocket соединений с поддержкой онлайн-статуса"""
    
    # TTL для Redis ключа онлайн-статуса (5 минут)
    ONLINE_STATUS_TTL = 300
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # keycloak_id -> connection_ids
        self.connection_users: Dict[str, str] = {}  # connection_id -> keycloak_id
        self.chat_subscriptions: Dict[str, Set[str]] = {}  # chat_id -> connection_ids
        self._lock = asyncio.Lock()
        self.redis_client: Optional[redis.Redis] = None
        self._redis_connected = False
        self.profile_client = get_profile_service_client()
        self.event_service = get_event_service()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
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
    
    async def start_heartbeat_checker(self):
        """Запуск фоновой задачи проверки heartbeat"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_checker())
            logger.info("Heartbeat checker started")
    
    async def stop_heartbeat_checker(self):
        """Остановка фоновой задачи проверки heartbeat"""
        self._shutdown = True
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat checker stopped")
    
    async def _heartbeat_checker(self):
        """Фоновая задача: проверка активных соединений каждую минуту"""
        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Проверка раз в минуту
                
                if self._shutdown:
                    break
                
                await self._cleanup_stale_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat checker: {e}")
    
    async def _cleanup_stale_connections(self):
        """Очистка "зависших" соединений (нет heartbeat более 5 минут)"""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return
            
            # Получаем все ключи онлайн-статуса
            keys = await redis_client.keys("user_online:*")
            current_time = datetime.utcnow()
            
            stale_connections = []
            
            for key in keys:
                keycloak_id = key.replace("user_online:", "")
                ttl = await redis_client.ttl(key)
                
                # Если TTL истек или ключ не существует
                if ttl <= 0:
                    # Проверяем, есть ли активные соединения в локальном кэше
                    async with self._lock:
                        has_active_connections = (
                            keycloak_id in self.user_connections and 
                            len(self.user_connections[keycloak_id]) > 0
                        )
                    
                    if not has_active_connections:
                        stale_connections.append(keycloak_id)
                        logger.warning(f"Stale connection detected for {keycloak_id}")
            
            # Отключаем зависшие соединения
            for keycloak_id in stale_connections:
                await self._force_disconnect_user(keycloak_id, reason="timeout")
                
        except Exception as e:
            logger.error(f"Error cleaning up stale connections: {e}")
    
    async def _force_disconnect_user(self, keycloak_id: str, reason: str = "timeout"):
        """Принудительное отключение пользователя по timeout"""
        logger.info(f"Force disconnecting user {keycloak_id} due to {reason}")
        
        # Публикуем событие OFFLINE
        await self.event_service.publish_user_offline(
            keycloak_id=keycloak_id,
            connection_id=None,
            reason=reason
        )
        
        # Удаляем из Redis
        try:
            redis_client = await self._get_redis()
            if redis_client:
                await redis_client.delete(f"user_online:{keycloak_id}")
        except Exception as e:
            logger.error(f"Error removing stale Redis key: {e}")
    
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
        """Подключение нового WebSocket клиента с установкой онлайн-статуса"""
        connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        async with self._lock:
            self.active_connections[connection_id] = websocket
            self.connection_users[connection_id] = keycloak_id
            
            if keycloak_id not in self.user_connections:
                self.user_connections[keycloak_id] = set()
            self.user_connections[keycloak_id].add(connection_id)
        
        # Устанавливаем онлайн-статус в Redis
        redis_client = await self._get_redis()
        if redis_client:
            try:
                # Устанавливаем ключ с TTL = 5 минут
                await redis_client.setex(
                    f"user_online:{keycloak_id}",
                    self.ONLINE_STATUS_TTL,
                    json.dumps({
                        "connection_id": connection_id,
                        "connected_at": datetime.utcnow().isoformat(),
                        "connections_count": len(self.user_connections[keycloak_id])
                    })
                )
            except Exception as e:
                logger.error(f"Failed to set online status in Redis: {e}")
        
        # Публикуем событие USER_ONLINE (только если это первое соединение)
        is_first_connection = len(self.user_connections[keycloak_id]) == 1
        if is_first_connection:
            await self.event_service.publish_user_online(
                keycloak_id=keycloak_id,
                connection_id=connection_id
            )
        
        logger.info(
            f"User {keycloak_id} connected with connection {connection_id[:8]}. "
            f"Total connections: {len(self.user_connections[keycloak_id])}"
        )
        
        # Запускаем heartbeat checker при первом подключении
        await self.start_heartbeat_checker()
        
        return connection_id
    
    async def disconnect(self, connection_id: str, reason: str = "disconnect"):
        """Отключение WebSocket клиента с очисткой онлайн-статуса"""
        async with self._lock:
            if connection_id not in self.connection_users:
                return
            
            keycloak_id = self.connection_users[connection_id]
            
            # Удаляем из активных соединений
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Удаляем из связей пользователь-соединение
            if keycloak_id in self.user_connections:
                self.user_connections[keycloak_id].discard(connection_id)
                remaining_connections = len(self.user_connections[keycloak_id])
                
                # Если это было последнее соединение пользователя
                if remaining_connections == 0:
                    del self.user_connections[keycloak_id]
                    is_last_connection = True
                else:
                    is_last_connection = False
            else:
                is_last_connection = True
            
            # Удаляем из отслеживания соединений
            del self.connection_users[connection_id]
            
            # Удаляем из подписок на чаты
            for chat_id in list(self.chat_subscriptions.keys()):
                self.chat_subscriptions[chat_id].discard(connection_id)
                if not self.chat_subscriptions[chat_id]:
                    del self.chat_subscriptions[chat_id]
        
        # Обновляем Redis только если это было последнее соединение
        if is_last_connection:
            try:
                redis_client = await self._get_redis()
                if redis_client:
                    await redis_client.delete(f"user_online:{keycloak_id}")
            except Exception as e:
                logger.error(f"Failed to remove online status from Redis: {e}")
            
            # Публикуем событие USER_OFFLINE
            await self.event_service.publish_user_offline(
                keycloak_id=keycloak_id,
                connection_id=connection_id,
                reason=reason
            )
            
            logger.info(f"User {keycloak_id} is now OFFLINE (last connection closed)")
        else:
            # Обновляем счетчик соединений в Redis
            try:
                redis_client = await self._get_redis()
                if redis_client:
                    await redis_client.setex(
                        f"user_online:{keycloak_id}",
                        self.ONLINE_STATUS_TTL,
                        json.dumps({
                            "connection_id": connection_id,
                            "updated_at": datetime.utcnow().isoformat(),
                            "connections_count": remaining_connections
                        })
                    )
            except Exception as e:
                logger.error(f"Failed to update connections count in Redis: {e}")
            
            logger.info(
                f"User {keycloak_id} disconnected from {connection_id[:8]}. "
                f"Remaining connections: {remaining_connections}"
            )
    
    async def handle_heartbeat(self, keycloak_id: str, connection_id: str):
        """Обработка heartbeat от клиента (ping)"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                # Продлеваем TTL ключа
                ttl = await redis_client.ttl(f"user_online:{keycloak_id}")
                if ttl > 0:
                    await redis_client.expire(
                        f"user_online:{keycloak_id}",
                        self.ONLINE_STATUS_TTL
                    )
                    logger.debug(f"Heartbeat processed for {keycloak_id}, TTL refreshed")
                else:
                    # Ключ истек, восстанавливаем
                    await redis_client.setex(
                        f"user_online:{keycloak_id}",
                        self.ONLINE_STATUS_TTL,
                        json.dumps({
                            "connection_id": connection_id,
                            "heartbeat_at": datetime.utcnow().isoformat()
                        })
                    )
                    logger.warning(f"Restored expired online status for {keycloak_id}")
            
            # Опционально: публикуем событие HEARTBEAT (для статистики)
            # await self.event_service.publish_user_heartbeat(keycloak_id, connection_id)
            
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
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
                            await self.disconnect(connection_id, reason="error")
    
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
                                await self.disconnect(connection_id, reason="error")
    
    async def send_typing_indicator(self, chat_id: str, user_id: str, is_typing: bool):
        """Отправка индикатора набора текста с display_name"""
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
        """Проверка онлайн статуса пользователя через Redis"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                online = await redis_client.exists(f"user_online:{keycloak_id}")
                return bool(online)
        except Exception as e:
            logger.error(f"Error checking online status in Redis: {e}")
        
        # Fallback: проверка локального кэша
        async with self._lock:
            return keycloak_id in self.user_connections and len(self.user_connections[keycloak_id]) > 0
    
    async def get_online_users(self) -> List[str]:
        """Получение списка онлайн пользователей из Redis"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                keys = await redis_client.keys("user_online:*")
                users = [key.replace("user_online:", "") for key in keys]
                return users
        except Exception as e:
            logger.error(f"Error getting online users from Redis: {e}")
        
        # Fallback: локальный кэш
        async with self._lock:
            return list(self.user_connections.keys())
    
    async def get_online_users_count(self) -> int:
        """Получение количества онлайн пользователей"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                keys = await redis_client.keys("user_online:*")
                return len(keys)
        except Exception as e:
            logger.error(f"Error getting online users count from Redis: {e}")
        
        # Fallback
        async with self._lock:
            return len(self.user_connections)
    
    def get_connection_count(self) -> int:
        """Получение количества активных соединений"""
        return len(self.active_connections)
    
    async def disconnect_all(self):
        """Отключение всех соединений (graceful shutdown)"""
        self._shutdown = True
        
        # Останавливаем heartbeat checker
        await self.stop_heartbeat_checker()
        
        # Публикуем offline для всех активных пользователей
        async with self._lock:
            active_users = list(self.user_connections.keys())
        
        for keycloak_id in active_users:
            await self.event_service.publish_user_offline(
                keycloak_id=keycloak_id,
                connection_id=None,
                reason="service_shutdown"
            )
        
        # Закрываем соединения
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
            
            # Очищаем Redis
            try:
                if self.redis_client:
                    keys = await self.redis_client.keys("user_online:*")
                    if keys:
                        await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Error clearing Redis on shutdown: {e}")
            
            logger.info("All WebSocket connections disconnected")

# Глобальный экземпляр менеджера
websocket_manager = ConnectionManager()