from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class RabbitMQConfig(BaseSettings):
    """Конфигурация RabbitMQ для всех сервисов"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="RABBITMQ__",
        case_sensitive=False,
    )
    
    host: str = "rabbitmq"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "/"
    
    @property
    def connection_url(self):
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"
    
    @property
    def management_url(self):
        return f"http://{self.host}:15672"