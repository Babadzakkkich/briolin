from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import quote_plus


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MEDIA__DB__",
        case_sensitive=False,
    )
    
    user: str = "media_user"
    password: str = "media_password"
    host: str = "media-postgres"
    port: int = 5432
    name: str = "media_db"
    
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 10

    @property
    def url(self):
        return (
            f"postgresql+asyncpg://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class MinIOConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MINIO__",
        case_sensitive=False,
    )
    
    endpoint: str = "minio:9000"
    access_key: str
    secret_key: str
    bucket_avatars: str = "avatars"
    secure: bool = False
    region: str = "us-east-1"
    
    @property
    def bucket(self) -> str:
        return self.bucket_avatars


class MediaServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MEDIA__",
        case_sensitive=False,
    )
    
    debug: bool = False
    service_name: str = "media-service"
    host: str = "0.0.0.0"
    port: int = 8007
    
    max_file_size: int = 5 * 1024 * 1024
    allowed_mime_types: list = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    ]
    max_width: int = 2000
    max_height: int = 2000
    thumbnail_size: int = 200
    
    max_avatars_per_user: int = 10


class Settings:
    def __init__(self):
        self.db = DatabaseConfig()
        self.minio = MinIOConfig()
        self.service = MediaServiceConfig()
    
    @property
    def debug(self) -> bool:
        return self.service.debug
    
    @property
    def service_name(self) -> str:
        return self.service.service_name
    
    @property
    def app_name(self) -> str:
        return "Briolin Media Service"


settings = Settings()