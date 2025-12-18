from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class KeycloakConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__KEYCLOAK__",
        case_sensitive=False,
    )
    server_url: str
    realm: str


class GatewayKeycloakConfig(BaseSettings):
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


class CacheConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CACHE__",
        case_sensitive=False,
    )
    redis_url: Optional[str] = "redis://redis:6379/0"
    user_cache_ttl: int = 60  # 1 минута для данных пользователя
    token_cache_ttl_buffer: int = 30  # 30 секунд буфер для TTL токенов


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    keycloak: KeycloakConfig = Field(default_factory=KeycloakConfig)
    gateway_keycloak: GatewayKeycloakConfig = Field(default_factory=GatewayKeycloakConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    services: ServicesConfig = Field(default_factory=ServicesConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

settings = Settings()