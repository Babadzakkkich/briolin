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
    service_name: str = "api-gateway"


class ServicesConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SERVICES__",
        case_sensitive=False,
    )
    auth: str
    user: str
    profile: str
    testing: str
    chat: str
    chat_ws: str
    search: str


class CacheConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CACHE__",
        case_sensitive=False,
    )
    redis_url: Optional[str] = "redis://redis:6379/0"
    user_cache_ttl: int = 60
    token_cache_ttl_buffer: int = 30


class Settings:
    """
    Композитная конфигурация api-gateway.
    Загружает специфичные настройки из env, shared - через get_shared_config().
    """
    
    def __init__(self):
        # Специфичные для gateway настройки (из env)
        self.gateway_keycloak = GatewayKeycloakClientConfig()
        self.gateway = GatewayConfig()
        self.services = ServicesConfig()
        self.cache = CacheConfig()
        
        # Shared настройки (через синглтон)
        self._shared = None
    
    @property
    def keycloak(self) -> KeycloakConfig:
        return get_shared_config().keycloak
    
    @property
    def shared_config(self):
        """Доступ к полному shared config если нужно"""
        if self._shared is None:
            self._shared = get_shared_config()
        return self._shared
    
    @property
    def service_name(self) -> str:
        return self.gateway.service_name


# Глобальный экземпляр
settings = Settings()