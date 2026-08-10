from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__POSTGRES__",
        case_sensitive=False,
    )
    
    user: str
    password: str
    host: str
    port: int = 5432
    name: str
    
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 10

    @property
    def url(self):
        return (
            f"postgresql+asyncpg://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__MONGO__",
        case_sensitive=False,
    )
    
    host: str
    port: int = 27017
    database: str
    
    @property
    def url(self):
        return f"mongodb://{self.host}:{self.port}"


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__REDIS__",
        case_sensitive=False,
    )
    url: str = "redis://redis:6379/1"


class WebSocketConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__WEBSOCKET__",
        case_sensitive=False,
    )
    
    timeout: int = 300
    message_rate_limit: int = 10
    message_rate_window: int = 60


class ExternalServicesConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__",
        case_sensitive=False,
    )
    
    user_service_url: str = "http://user-service:8002"
    profile_service_url: str = "http://profile-service:8003"


class ChatServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__",
        case_sensitive=False,
    )
    
    debug: bool = True
    service_name: str = "chat-service"


class Settings:
    def __init__(self):
        self.service = ChatServiceConfig()
        self.postgres = PostgresConfig()
        self.mongo = MongoConfig()
        self.redis = RedisConfig()
        self.websocket = WebSocketConfig()
        self.external = ExternalServicesConfig()
    
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
        return "Briolin Chat Service"
    
    @property
    def user_service_url(self) -> str:
        return self.external.user_service_url
    
    @property
    def profile_service_url(self) -> str:
        return self.external.profile_service_url


settings = Settings()