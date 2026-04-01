from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.rabbitmq.consumer import RabbitMQConsumer
from app.core.config import settings

# Используем общую конфигурацию RabbitMQ из shared
from shared.config import get_shared_config

rabbitmq_config = get_shared_config().rabbitmq

# Publisher для отправки событий
rabbitmq_publisher = RabbitMQPublisher(rabbitmq_config)

# Consumer для получения событий
rabbitmq_consumer = RabbitMQConsumer(rabbitmq_config, settings.service_name)