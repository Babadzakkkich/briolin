from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig

class PostgresConfig(BaseModel):
    """Конфигурация PostgreSQL"""
    user: str = Field(..., env="CHAT__DB__USER")
    password: str = Field(..., env="CHAT__DB__PASSWORD")
    host: str = Field(..., env="CHAT__DB__HOST")
    port: int = Field(..., env="CHAT__DB__PORT")
    name: str = Field(..., env="CHAT__DB__NAME")
    
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 10

    @property
    def url(self):
        return (
            f"postgresql+asyncpg://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )

class MongoConfig(BaseModel):
    """Конфигурация MongoDB"""
    host: str = Field(..., env="CHAT__MONGO__HOST")
    port: int = Field(..., env="CHAT__MONGO__PORT")
    database: str = Field(..., env="CHAT__MONGO__DATABASE")
    
    @property
    def url(self):
        return f"mongodb://{self.host}:{self.port}"

class RedisConfig(BaseModel):
    """Конфигурация Redis для кэширования и rate limiting"""
    url: str = Field("redis://redis:6379/1", env="CHAT__REDIS_URL")

class WebSocketConfig(BaseModel):
    """Конфигурация WebSocket"""
    timeout: int = Field(300, env="CHAT__WEBSOCKET_TIMEOUT")
    message_rate_limit: int = Field(10, env="CHAT__MESSAGE_RATE_LIMIT")
    message_rate_window: int = Field(60, env="CHAT__MESSAGE_RATE_WINDOW")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CHAT__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )

    app_name: str = "Briolin Chat Service"
    service_name: str = "chat-service"
    debug: bool = True

    keycloak: KeycloakConfig = Field(default_factory=lambda: get_shared_config().keycloak)
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: get_shared_config().rabbitmq)
    postgres: PostgresConfig = Field(...)
    mongo: MongoConfig = Field(...)
    redis: RedisConfig = Field(...)
    websocket: WebSocketConfig = Field(...)
    
    # URL сервисов
    user_service_url: str = Field("http://user-service:8002", env="CHAT__USER_SERVICE__URL")
    profile_service_url: str = Field("http://profile-service:8003", env="CHAT__PROFILE_SERVICE__URL")

settings = Settings()