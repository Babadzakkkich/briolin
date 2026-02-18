from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class KeycloakConfig(BaseModel):
    server_url: Optional[str] = Field(None, env="KEYCLOAK__SERVER_URL")
    realm: Optional[str] = Field(None, env="KEYCLOAK__REALM")


class RabbitMQConfig(BaseModel):
    host: str = Field(..., env="RABBITMQ__HOST")
    port: int = Field(..., env="RABBITMQ__PORT")
    user: str = Field(..., env="RABBITMQ__USER")
    password: str = Field(..., env="RABBITMQ__PASSWORD")
    vhost: str = Field(..., env="RABBITMQ__VHOST")
    
    @property
    def connection_url(self):
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class SharedConfig(BaseSettings):
    """
    Общая конфигурация, загружаемая исключительно из переменных окружения.
    Keycloak опционален (для сервисов которые его не используют).
    """
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    
    keycloak: Optional[KeycloakConfig] = Field(default_factory=KeycloakConfig)
    rabbitmq: RabbitMQConfig = Field(...)


# Синглтон с ленивой инициализацией
_shared_config_instance = None

def get_shared_config() -> SharedConfig:
    global _shared_config_instance
    if _shared_config_instance is None:
        _shared_config_instance = SharedConfig()
    return _shared_config_instance


__all__ = ['get_shared_config', 'KeycloakConfig', 'RabbitMQConfig', 'SharedConfig']