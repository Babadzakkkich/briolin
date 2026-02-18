import asyncio
import json
import logging
import aio_pika
from typing import Dict, Any, Callable, Awaitable, Optional
from contextlib import asynccontextmanager
from .config import RabbitMQConfig
from shared.events.schemas import EventType

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """Асинхронный consumer для RabbitMQ"""
    
    def __init__(self, config: RabbitMQConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self._lock = asyncio.Lock()
        self._is_connected = False
        self._consumers = {}
    
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
                    await self.channel.set_qos(prefetch_count=10)
                    self._is_connected = True
                    logger.info(f"RabbitMQ consumer connected for {self.service_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to connect to RabbitMQ consumer: {e}")
                    self._is_connected = False
                    raise
    
    async def disconnect(self):
        """Закрытие соединения и отмена всех consumers"""
        async with self._lock:
            for queue_name, consumer_tag in self._consumers.items():
                if consumer_tag:
                    await self.channel.basic_cancel(consumer_tag)
            
            if self._is_connected:
                if self.channel:
                    await self.channel.close()
                if self.connection:
                    await self.connection.close()
                self._is_connected = False
                logger.info(f"RabbitMQ consumer disconnected for {self.service_name}")
    
    @asynccontextmanager
    async def ensure_connection(self):
        """Контекстный менеджер для гарантии соединения"""
        if not self._is_connected:
            await self.connect()
        yield
    
    async def consume(
        self,
        exchange_name: str,
        routing_key: str,
        queue_name: str,
        callback: Callable[[Dict[str, Any]], Awaitable[bool]],
        durable: bool = True,
        auto_ack: bool = False
    ):
        """Подписка на сообщения из RabbitMQ"""
        try:
            async with self.ensure_connection():
                exchange = await self.channel.declare_exchange(
                    name=exchange_name,
                    type=aio_pika.ExchangeType.TOPIC,
                    durable=durable
                )
                
                queue = await self.channel.declare_queue(
                    name=queue_name,
                    durable=durable,
                    arguments={
                        "x-dead-letter-exchange": f"{exchange_name}.dlx",
                        "x-dead-letter-routing-key": routing_key
                    }
                )
                
                await queue.bind(exchange, routing_key=routing_key)
                
                async def message_handler(message: aio_pika.IncomingMessage):
                    processed = False
                    try:
                        body = json.loads(message.body.decode())
                        logger.debug(
                            f"Message received on {queue_name} [{routing_key}]: "
                            f"{body.get('event_type', 'unknown')}"
                        )
                        
                        success = await callback(body)
                        
                        if success:
                            await message.ack()
                            logger.debug(f"Message processed successfully: {body.get('event_type')}")
                        else:
                            await message.nack(requeue=False)
                            logger.error(f"Message processing failed: {body.get('event_type')}")
                        
                        processed = True
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        await message.reject(requeue=False)
                        processed = True
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        if not processed:
                            await message.nack(requeue=True)
                        else:
                            logger.warning(f"Message already processed, ignoring error: {e}")
                
                consumer_tag = await queue.consume(
                    message_handler,
                    no_ack=auto_ack
                )
                self._consumers[queue_name] = consumer_tag
                
                logger.info(
                    f"Consumer started for queue '{queue_name}' "
                    f"on exchange '{exchange_name}' with routing key '{routing_key}'"
                )
                
        except Exception as e:
            logger.error(f"Failed to start consumer for {routing_key}: {e}")
            raise
    
    async def consume_user_events(
        self,
        event_type: EventType,
        callback: Callable[[Dict[str, Any]], Awaitable[bool]]
    ):
        """Подписка на события пользователей с использованием Enum"""
        queue_name = f"{self.service_name}.{event_type.value}"
        routing_key = event_type.value
        
        logger.info(f"Subscribing to queue: {queue_name} with routing key: {routing_key}")
        
        await self.consume(
            exchange_name="briolin.events",
            routing_key=routing_key,
            queue_name=queue_name,
            callback=callback
        )