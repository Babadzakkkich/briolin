import asyncio
import json
from typing import Optional

import aio_pika

from app.core.config import settings
from app.core.logger import logger
from app.services.email_service import EmailService
from app.schemas.email import EmailType


email_service = EmailService()
_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None
_consumer_task: Optional[asyncio.Task] = None
_running = False


async def process_email_message(message: aio_pika.IncomingMessage):
    """Обработка сообщения из RabbitMQ"""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            logger.info(f"Received email notification: {data.get('type')} for {data.get('to')}")
            
            email_type = data.get("type")
            to_email = data.get("to")
            
            if not email_type or not to_email:
                logger.error(f"Invalid email message: missing type or to")
                return
            
            # Преобразуем тип
            try:
                email_type_enum = EmailType(email_type)
            except ValueError:
                logger.error(f"Unknown email type: {email_type}")
                return
            
            # Отправляем email
            await email_service.send_template_email(
                to_email=to_email,
                template_name=email_type_enum,
                context=data
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Failed to process email: {e}")


async def start_consumer():
    """Запуск RabbitMQ consumer"""
    global _connection, _channel, _consumer_task, _running
    
    if _running:
        logger.warning("Consumer already running")
        return
    
    try:
        rabbitmq_config = settings.rabbitmq
        url = f"amqp://{rabbitmq_config.user}:{rabbitmq_config.password}@{rabbitmq_config.host}:{rabbitmq_config.port}/"
        
        _connection = await aio_pika.connect_robust(url)
        _channel = await _connection.channel()
        
        # Объявляем очередь
        queue = await _channel.declare_queue(
            settings.queue_name,
            durable=True
        )
        
        _running = True
        
        async def consume():
            await queue.consume(process_email_message)
            logger.info(f"Email consumer started, listening on queue: {settings.queue_name}")
            await asyncio.Future()  # Бесконечно ждем
        
        _consumer_task = asyncio.create_task(consume())
        
    except Exception as e:
        logger.error(f"Failed to start email consumer: {e}")
        _running = False
        raise


async def stop_consumer():
    """Остановка RabbitMQ consumer"""
    global _connection, _channel, _consumer_task, _running
    
    _running = False
    
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        _consumer_task = None
    
    if _channel:
        await _channel.close()
        _channel = None
    
    if _connection:
        await _connection.close()
        _connection = None
    
    logger.info("Email consumer stopped")


def is_consumer_running() -> bool:
    return _running