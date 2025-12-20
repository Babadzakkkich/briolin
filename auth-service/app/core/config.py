# APP/CORE/CONFIG.PY (auth-service)
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from shared.config import get_shared_config, KeycloakConfig

# Делаем AuthKeycloakClientConfig BaseSettings
class AuthKeycloakClientConfig(BaseSettings):
    """Конфигурация клиента Keycloak для auth-service (client_id и client_secret)"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__KEYCLOAK__",
        case_sensitive=False,
    )
    
    client_id: str
    client_secret: str
    default_role: str = "user"

class DatabaseConfig(BaseModel):
    user: str = Field(..., env="AUTH__DB__USER")
    password: str = Field(..., env="AUTH__DB__PASSWORD")
    host: str = Field(..., env="AUTH__DB__HOST")
    port: int = Field(..., env="AUTH__DB__PORT")
    name: str = Field(..., env="AUTH__DB__NAME")
    
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

class UserServiceConfig(BaseModel):
    url: str = Field(..., env="AUTH__USER_SERVICE__URL")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__",
        case_sensitive=False,
        extra='allow'  # Разрешаем дополнительные поля
    )

    app_name: str = "Briolin Auth Service"
    debug: bool = Field(..., env="AUTH__DEBUG")

    # Используем AuthKeycloakClientConfig как BaseSettings
    keycloak_client: AuthKeycloakClientConfig = Field(default_factory=AuthKeycloakClientConfig)
    db: DatabaseConfig = Field(...)
    user_service: UserServiceConfig = Field(...)
    
    # Делаем keycloak свойством
    @property
    def keycloak(self) -> KeycloakConfig:
        return get_shared_config().keycloak

settings = Settings()