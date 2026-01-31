from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.rabbitmq.consumer import RabbitMQConsumer
from app.core.config import settings

# Publisher для отправки событий
rabbitmq_publisher = RabbitMQPublisher(settings.rabbitmq)

# Consumer для получения событий от других сервисов
rabbitmq_consumer = RabbitMQConsumer(settings.rabbitmq, "testing-service")