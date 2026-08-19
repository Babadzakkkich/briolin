from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from typing import Optional
from shared.config import get_shared_config, RabbitMQConfig


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="TESTING__DB__",
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


class MongoDBConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="TESTING__MONGO__",
        case_sensitive=False,
    )
    
    host: str
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    database: str
    
    @property
    def url(self):
        if self.username and self.password:
            return f"mongodb://{self.username}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"
        return f"mongodb://{self.host}:{self.port}/{self.database}"


class TestConfig(BaseSettings):
    """Локальные настройки тестов (не из env, дефолты)"""
    default_test_size: int = 10
    question_pool_size: int = 15
    max_attempts_per_day: int = 30
    test_time_limit_minutes: int = 30


class TestingServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="TESTING__",
        case_sensitive=False,
    )
    
    debug: bool = True
    service_name: str = "testing-service"


class Settings:
    def __init__(self):
        self.service = TestingServiceConfig()
        self.db = DatabaseConfig()
        self.mongo = MongoDBConfig()
        self.test_config = TestConfig()
    
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
        return "Briolin Testing Service"
    
    @property
    def version(self) -> str:
        return "1.0.0"


settings = Settings()