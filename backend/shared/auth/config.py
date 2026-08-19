from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedAuthConfig(BaseModel):
    """Конфигурация для общей аутентификации (JWT)"""
    jwt_secret: str = Field(..., env="SHARED__JWT_SECRET")
    jwt_algorithm: str = Field(..., env="SHARED__JWT_ALGORITHM")
    jwt_issuer: str = Field(..., env="SHARED__JWT_ISSUER")
    jwt_audience: str = Field(..., env="SHARED__JWT_AUDIENCE")
    jwt_expire_minutes: int = Field(..., env="SHARED__JWT_EXPIRE_MINUTES")


class Settings(BaseSettings):
    """
    Настройки shared.auth - только переменные окружения.
    """
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    
    shared: SharedAuthConfig = Field(default_factory=SharedAuthConfig)


settings = Settings()