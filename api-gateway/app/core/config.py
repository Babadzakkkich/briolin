# APP/CORE/CONFIG.PY (api-gateway)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from shared.config import get_shared_config, KeycloakConfig

class GatewayKeycloakClientConfig(BaseSettings):
    """Конфигурация клиента Keycloak для api-gateway"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="GATEWAY__KEYCLOAK__",
        case_sensitive=False,
    )
    client_id: str
    client_secret: str

class GatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="GATEWAY__",
        case_sensitive=False,
    )
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

class ServicesConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SERVICES__",
        case_sensitive=False,
    )
    auth: str
    user: str

class CacheConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CACHE__",
        case_sensitive=False,
    )
    redis_url: Optional[str] = "redis://redis:6379/0"
    user_cache_ttl: int = 60
    token_cache_ttl_buffer: int = 30

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Используем общую конфигурацию Keycloak
    keycloak: KeycloakConfig = Field(default_factory=lambda: get_shared_config().keycloak)
    # Плюс специфичные для api-gateway настройки клиента
    gateway_keycloak: GatewayKeycloakClientConfig = Field(default_factory=GatewayKeycloakClientConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    services: ServicesConfig = Field(default_factory=ServicesConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

settings = Settings()