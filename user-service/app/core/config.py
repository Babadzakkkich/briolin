from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from typing import ClassVar
from shared.config import get_shared_config, KeycloakConfig, RabbitMQConfig

class DatabaseConfig(BaseModel):
    user: str = Field(..., env="USER__DB__USER")
    password: str = Field(..., env="USER__DB__PASSWORD")
    host: str = Field(..., env="USER__DB__HOST")
    port: int = Field(..., env="USER__DB__PORT")
    name: str = Field(..., env="USER__DB__NAME")
    
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

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="USER__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )

    app_name: str = "Briolin User Service"
    debug: bool = Field(False, env="USER__DEBUG")

    keycloak: KeycloakConfig = Field(default_factory=lambda: get_shared_config().keycloak)
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: get_shared_config().rabbitmq)
    db: DatabaseConfig = Field(...)
    
    auth_service_url: str = Field("http://auth-service:8001", env="USER__AUTH_SERVICE__URL")

settings = Settings()