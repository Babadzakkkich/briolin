from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from typing import Optional
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SEARCH__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Основные настройки сервиса
    app_name: str = "Briolin Search Service"
    service_name: str = "search-service"
    debug: bool = Field(False, validation_alias="SEARCH__DEBUG")

    # Shared конфигурация
    keycloak: KeycloakConfig = Field(default_factory=lambda: get_shared_config().keycloak)
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: get_shared_config().rabbitmq)

    # Своя БД (для search_sessions)
    db_user: str = Field(..., validation_alias="SEARCH__DB__USER")
    db_password: str = Field(..., validation_alias="SEARCH__DB__PASSWORD")
    db_host: str = Field(..., validation_alias="SEARCH__DB__HOST")
    db_port: int = Field(..., validation_alias="SEARCH__DB__PORT")
    db_name: str = Field(..., validation_alias="SEARCH__DB__NAME")
    db_echo: bool = Field(False, validation_alias="SEARCH__DB__ECHO")
    db_pool_size: int = Field(20, validation_alias="SEARCH__DB__POOL_SIZE")
    db_max_overflow: int = Field(10, validation_alias="SEARCH__DB__MAX_OVERFLOW")

    @property
    def db_url(self) -> str:
        """URL для подключения к своей БД"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # URL сервисов
    profile_service_url: str = Field(..., validation_alias="SEARCH__PROFILE_SERVICE__URL")
    auth_service_url: Optional[str] = Field(None, validation_alias="SEARCH__AUTH_SERVICE__URL")


settings = Settings()