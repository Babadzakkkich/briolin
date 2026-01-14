from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from typing import ClassVar
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig

class DatabaseConfig(BaseModel):
    user: str = Field(..., env="PROFILE__DB__USER")
    password: str = Field(..., env="PROFILE__DB__PASSWORD")
    host: str = Field(..., env="PROFILE__DB__HOST")
    port: int = Field(..., env="PROFILE__DB__PORT")
    name: str = Field(..., env="PROFILE__DB__NAME")
    
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

class AuthServiceConfig(BaseModel):
    url: str = Field(..., env="PROFILE__AUTH_SERVICE__URL")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="PROFILE__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )

    app_name: str = "Briolin Profile Service"
    service_name: str = "profile-service"
    debug: bool = Field(False, env="PROFILE__DEBUG")

    keycloak: KeycloakConfig = Field(default_factory=lambda: get_shared_config().keycloak)
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: get_shared_config().rabbitmq)
    db: DatabaseConfig = Field(...)
    auth_service: AuthServiceConfig = Field(...)

settings = Settings()