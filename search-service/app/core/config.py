from pydantic import BaseModel, Field
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

    # Своя БД (для search_sessions) - используется в own_db
    own_db_user: str = Field(..., validation_alias="SEARCH__OWN_DB__USER")
    own_db_password: str = Field(..., validation_alias="SEARCH__OWN_DB__PASSWORD")
    own_db_host: str = Field(..., validation_alias="SEARCH__OWN_DB__HOST")
    own_db_port: int = Field(..., validation_alias="SEARCH__OWN_DB__PORT")
    own_db_name: str = Field(..., validation_alias="SEARCH__OWN_DB__NAME")
    own_db_echo: bool = Field(False, validation_alias="SEARCH__OWN_DB__ECHO")
    own_db_pool_size: int = Field(20, validation_alias="SEARCH__OWN_DB__POOL_SIZE")
    own_db_max_overflow: int = Field(10, validation_alias="SEARCH__OWN_DB__MAX_OVERFLOW")

    @property
    def own_db_url(self) -> str:
        """URL для подключения к своей БД"""
        return (
            f"postgresql+asyncpg://{self.own_db_user}:{quote_plus(self.own_db_password)}"
            f"@{self.own_db_host}:{self.own_db_port}/{self.own_db_name}"
        )

    # БД profile-service (только чтение) - используется в profile_db
    profile_db_user: str = Field(..., validation_alias="SEARCH__PROFILE_DB__USER")
    profile_db_password: str = Field(..., validation_alias="SEARCH__PROFILE_DB__PASSWORD")
    profile_db_host: str = Field(..., validation_alias="SEARCH__PROFILE_DB__HOST")
    profile_db_port: int = Field(..., validation_alias="SEARCH__PROFILE_DB__PORT")
    profile_db_name: str = Field(..., validation_alias="SEARCH__PROFILE_DB__NAME")
    profile_db_echo: bool = Field(False, validation_alias="SEARCH__PROFILE_DB__ECHO")
    profile_db_pool_size: int = Field(20, validation_alias="SEARCH__PROFILE_DB__POOL_SIZE")
    profile_db_max_overflow: int = Field(10, validation_alias="SEARCH__PROFILE_DB__MAX_OVERFLOW")

    @property
    def profile_db_url(self) -> str:
        """URL для подключения к БД profile-service"""
        return (
            f"postgresql+asyncpg://{self.profile_db_user}:{quote_plus(self.profile_db_password)}"
            f"@{self.profile_db_host}:{self.profile_db_port}/{self.profile_db_name}"
        )

    # Auth service (опционально, может пригодиться)
    auth_service_url: Optional[str] = Field(None, validation_alias="SEARCH__AUTH_SERVICE__URL")


settings = Settings()