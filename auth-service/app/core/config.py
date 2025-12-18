from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class KeycloakConfig(BaseModel):
    server_url: str = Field(..., env="AUTH__KEYCLOAK__SERVER_URL")
    realm: str = Field(..., env="AUTH__KEYCLOAK__REALM")
    client_id: str = Field(..., env="AUTH__KEYCLOAK__CLIENT_ID")
    client_secret: str = Field(..., env="AUTH__KEYCLOAK__CLIENT_SECRET")
    
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

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__",
        case_sensitive=False,
    )

    app_name: str = "Briolin Auth Service"
    debug: bool = Field(..., env="AUTH__DEBUG")

    keycloak: KeycloakConfig = Field(...)
    db: DatabaseConfig = Field(...)

settings = Settings()