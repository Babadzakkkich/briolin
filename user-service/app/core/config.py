from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class KeycloakConfig(BaseModel):
    server_url: str = Field(..., env="KEYCLOAK__SERVER_URL")
    realm: str = Field(..., env="KEYCLOAK__REALM")
    client_id: str = Field(..., env="USER__KEYCLOAK__CLIENT_ID")
    client_secret: str = Field(..., env="USER__KEYCLOAK__CLIENT_SECRET")

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
    )

    app_name: str = "Briolin User Service"
    debug: bool = Field(..., env="USER__DEBUG")

    keycloak: KeycloakConfig = Field(...)
    db: DatabaseConfig = Field(...)

settings = Settings()