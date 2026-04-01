from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


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
    
    # Ограничения на загрузку
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_mime_types: list = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    ]
    max_width: int = 2000
    max_height: int = 2000
    thumbnail_size: int = 200


class Settings:
    def __init__(self):
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