from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.rabbitmq.consumer import RabbitMQConsumer
from app.core.config import settings

rabbitmq_publisher = RabbitMQPublisher(settings.rabbitmq)
rabbitmq_consumer = RabbitMQConsumer(settings.rabbitmq, "matching-service")