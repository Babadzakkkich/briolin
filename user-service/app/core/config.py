from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="USER__DB__",
        case_sensitive=False,
    )
    
    user: str
    password: str
    host: str
    port: int = 5432
    name: str
    
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    @property
    def url(self):
        return (
            f"postgresql+asyncpg://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class UserServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="USER__",
        case_sensitive=False,
    )
    
    debug: bool = False
    service_name: str = "user-service"
    auth_service_url: str = "http://auth-service:8001"


class Settings:
    def __init__(self):
        self.service = UserServiceConfig()
        self.db = DatabaseConfig()
    
    @property
    def keycloak(self) -> KeycloakConfig:
        return get_shared_config().keycloak
    
    @property
    def rabbitmq(self) -> RabbitMQConfig:
        return get_shared_config().rabbitmq
    
    @property
    def debug(self) -> bool:
        return self.service.debug
    
    @property
    def service_name(self) -> str:
        return self.service.service_name
    
    @property
    def app_name(self) -> str:
        return "Briolin User Service"
    
    @property
    def auth_service_url(self) -> str:
        return self.service.auth_service_url


settings = Settings()