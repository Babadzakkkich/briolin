from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from urllib.parse import quote_plus
from typing import Optional
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MATCHING__DB__",
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
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MATCHING__REDIS__",
        case_sensitive=False,
    )
    url: str = "redis://redis:6379/2"


class ServicesConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    profile_service_url: str = "http://profile-service:8003"
    search_service_url: str = "http://search-service:8006"
    chat_service_url: str = "http://chat-service:8005"


class SwipeLimitsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MATCHING__",
        case_sensitive=False,
    )
    daily_limit: int = 100


class MatchingServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MATCHING__",
        case_sensitive=False,
    )
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8010
    service_name: str = "matching-service"


class Settings:
    def __init__(self):
        self.service = MatchingServiceConfig()
        self.db = DatabaseConfig()
        self.redis = RedisConfig()
        self.services = ServicesConfig()
        self.limits = SwipeLimitsConfig()

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


settings = Settings()