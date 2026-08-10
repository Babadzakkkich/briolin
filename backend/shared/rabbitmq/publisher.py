import asyncio
import json
import aio_pika
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from .config import RabbitMQConfig
import logging
from shared.events.schemas import EventType, BaseEvent

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
    
    async def publish_event(self, event: BaseEvent) -> bool:
        """Публикация события в RabbitMQ"""
        for attempt in range(3):
            try:
                async with self.ensure_connection():
                    exchange = await self.channel.declare_exchange(
                        name="briolin.events",
                        type=aio_pika.ExchangeType.TOPIC,
                        durable=True
                    )
                    
                    message_body = json.dumps({
                        **event.model_dump(),
                        "timestamp": datetime.utcnow().isoformat(),
                        "message_id": f"msg_{datetime.utcnow().timestamp()}"
                    }).encode()
                    
                    rabbitmq_message = aio_pika.Message(
                        body=message_body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        content_type="application/json",
                        content_encoding="utf-8"
                    )
                    
                    await exchange.publish(
                        message=rabbitmq_message,
                        routing_key=event.event_type.value
                    )
                    
                    logger.debug(
                        f"Event published: {event.event_type.value} "
                        f"from {event.source_service}"
                    )
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to publish event (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                    await self.connect()
                else:
                    logger.error(f"All attempts failed for event: {event.event_type}")
                    return False
    
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