from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from shared.config import get_shared_config, KeycloakConfig


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class GatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="GATEWAY__",
        case_sensitive=False,
        extra="ignore",
    )
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    service_name: str = "api-gateway"

    # При cookie-авторизации нельзя использовать allow_origins=["*"] вместе
    # с allow_credentials=True. Указывай реальные адреса frontend через запятую.
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return _split_csv(self.cors_origins)


class GatewayCookieConfig(BaseSettings):
    """Настройки cookies для браузерной авторизации через API Gateway."""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="GATEWAY__COOKIE__",
        case_sensitive=False,
        extra="ignore",
    )

    access_cookie_name: str = "briolin_access_token"
    refresh_cookie_name: str = "briolin_refresh_token"

    path: str = "/"
    domain: Optional[str] = None

    # Для локальной разработки по http оставляем False.
    # Для продакшена с HTTPS нужно поставить True.
    secure: bool = False

    # Для localhost/одного сайта обычно достаточно lax.
    # Если frontend и API находятся на разных сайтах и нужны cross-site cookies,
    # используй samesite=none вместе с secure=True.
    samesite: str = "lax"


class ServicesConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SERVICES__",
        case_sensitive=False,
        extra="ignore",
    )
    auth: str
    user: str
    profile: str
    testing: str
    chat: str
    chat_ws: str
    media: Optional[str] = None
    matching: Optional[str] = None


class CacheConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="CACHE__",
        case_sensitive=False,
        extra="ignore",
    )
    redis_url: Optional[str] = "redis://redis:6379/0"
    user_cache_ttl: int = 60
    token_cache_ttl_buffer: int = 30


class Settings:
    """
    Композитная конфигурация api-gateway.

    Gateway больше не требует собственного Keycloak client_id/client_secret для
    проверки пользовательских access tokens. Проверка выполняется локально по
    JWT-подписи и JWKS публичным ключам realm.
    """

    def __init__(self):
        self.gateway = GatewayConfig()
        self.cookies = GatewayCookieConfig()
        self.services = ServicesConfig()
        self.cache = CacheConfig()
        self._shared = None

    @property
    def keycloak(self) -> KeycloakConfig:
        return get_shared_config().keycloak

    @property
    def shared_config(self):
        """Доступ к полному shared config если нужно."""
        if self._shared is None:
            self._shared = get_shared_config()
        return self._shared

    @property
    def service_name(self) -> str:
        return self.gateway.service_name


settings = Settings()
