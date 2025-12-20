# shared/config.py
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class KeycloakConfig(BaseModel):
    server_url: str = Field(..., env="KEYCLOAK__SERVER_URL")
    realm: str = Field(..., env="KEYCLOAK__REALM")

class SharedConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    keycloak: KeycloakConfig = Field(...)

# Создаем экземпляр один раз
_shared_config_instance = None

def get_shared_config() -> SharedConfig:
    """Функция для получения экземпляра общей конфигурации"""
    global _shared_config_instance
    if _shared_config_instance is None:
        _shared_config_instance = SharedConfig()
    return _shared_config_instance

# Экспортируем функцию и тип
__all__ = ['get_shared_config', 'KeycloakConfig', 'SharedConfig']