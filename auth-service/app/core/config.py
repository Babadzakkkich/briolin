from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig


class AuthKeycloakClientConfig(BaseSettings):
    """Конфигурация клиента Keycloak для auth-service"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__KEYCLOAK__",
        case_sensitive=False,
    )
    
    client_id: str
    client_secret: str
    default_role: str = "user"


class DatabaseConfig(BaseSettings):
    """Database config с префиксом AUTH__DB__"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__DB__",
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
        env_prefix="AUTH__USER_SERVICE__",
        case_sensitive=False,
    )
    url: str


class AuthServiceConfig(BaseSettings):
    """Основные настройки auth-service"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__",
        case_sensitive=False,
    )
    
    debug: bool = True
    service_name: str = "auth-service"


class Settings:
    """
    Композитная конфигурация auth-service.
    """
    
    def __init__(self):
        self.service = AuthServiceConfig()
        self.keycloak_client = AuthKeycloakClientConfig()
        self.db = DatabaseConfig()
        self.user_service = UserServiceConfig()
    
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
        return "Briolin Auth Service"


settings = Settings()