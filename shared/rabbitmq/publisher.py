import asyncio
import json
import aio_pika
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from .config import RabbitMQConfig
import logging

logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    """Асинхронный publisher для RabbitMQ"""
    
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self._lock = asyncio.Lock()
        self._is_connected = False
    
    async def connect(self):
        """Установка соединения с RabbitMQ"""
        async with self._lock:
            if not self._is_connected:
                try:
                    self.connection = await aio_pika.connect_robust(
                        self.config.connection_url,
                        timeout=10
                    )
                    self.channel = await self.connection.channel()
                    self._is_connected = True
                    logger.info("RabbitMQ publisher connected successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to connect to RabbitMQ: {e}")
                    self._is_connected = False
                    raise
    
    async def disconnect(self):
        """Закрытие соединения"""
        async with self._lock:
            if self._is_connected:
                if self.channel:
                    await self.channel.close()
                if self.connection:
                    await self.connection.close()
                self._is_connected = False
                logger.info("RabbitMQ publisher disconnected")
    
    @asynccontextmanager
    async def ensure_connection(self):
        """Контекстный менеджер для гарантии соединения"""
        if not self._is_connected:
            await self.connect()
        yield
    
    async def publish(
        self,
        exchange_name: str,
        routing_key: str,
        message: Dict[str, Any],
        durable: bool = True,
        retry_count: int = 3
    ) -> bool:
        """Публикация сообщения в RabbitMQ"""
        for attempt in range(retry_count):
            try:
                async with self.ensure_connection():
                    # Объявляем exchange
                    exchange = await self.channel.declare_exchange(
                        name=exchange_name,
                        type=aio_pika.ExchangeType.TOPIC,
                        durable=durable
                    )
                    
                    # Подготавливаем сообщение
                    message_body = json.dumps({
                        **message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message_id": f"msg_{datetime.utcnow().timestamp()}"
                    }).encode()
                    
                    rabbitmq_message = aio_pika.Message(
                        body=message_body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT if durable else aio_pika.DeliveryMode.TRANSIENT,
                        content_type="application/json",
                        content_encoding="utf-8"
                    )
                    
                    # Публикуем сообщение
                    await exchange.publish(
                        message=rabbitmq_message,
                        routing_key=routing_key
                    )
                    
                    logger.debug(
                        f"Message published to {exchange_name}.{routing_key}: "
                        f"{message.get('event_type', 'unknown')}"
                    )
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to publish message (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)  # Exponential backoff можно добавить
                    await self.connect()  # Переподключаемся
                else:
                    logger.error(f"All {retry_count} attempts failed for routing_key: {routing_key}")
                    return False
    
    async def publish_user_event(
        self,
        event_type: str,
        user_data: Dict[str, Any],
        routing_key_suffix: Optional[str] = None
    ) -> bool:
        """Публикация события, связанного с пользователем"""
        routing_key = f"user.{event_type}"
        if routing_key_suffix:
            routing_key = f"{routing_key}.{routing_key_suffix}"
        
        message = {
            "event_type": event_type,
            "event_source": "user-service",  # или другой сервис
            "user_data": user_data,
            "version": "1.0"
        }
        
        return await self.publish(
            exchange_name="briolin.events",
            routing_key=routing_key,
            message=message
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья подключения"""
        try:
            async with self.ensure_connection():
                return {
                    "status": "connected",
                    "host": self.config.host,
                    "channel_open": self.channel.is_open if self.channel else False
                }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "host": self.config.host
            }