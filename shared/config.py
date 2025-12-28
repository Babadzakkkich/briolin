from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class KeycloakConfig(BaseModel):
    server_url: str = Field(..., env="KEYCLOAK__SERVER_URL")
    realm: str = Field(..., env="KEYCLOAK__REALM")

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
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    keycloak: KeycloakConfig = Field(...)
    rabbitmq: RabbitMQConfig = Field(...)

# Создаем экземпляр один раз
_shared_config_instance = None

def get_shared_config() -> SharedConfig:
    global _shared_config_instance
    if _shared_config_instance is None:
        _shared_config_instance = SharedConfig()
    return _shared_config_instance

__all__ = ['get_shared_config', 'KeycloakConfig', 'RabbitMQConfig', 'SharedConfig']