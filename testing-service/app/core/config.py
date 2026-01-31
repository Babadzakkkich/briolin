from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from typing import Optional
from shared.config import get_shared_config, RabbitMQConfig

class DatabaseConfig(BaseModel):
    user: str = Field(..., env="TESTING__DB__USER")
    password: str = Field(..., env="TESTING__DB__PASSWORD")
    host: str = Field(..., env="TESTING__DB__HOST")
    port: int = Field(..., env="TESTING__DB__PORT")
    name: str = Field(..., env="TESTING__DB__NAME")
    
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

class MongoDBConfig(BaseModel):
    host: str = Field(..., env="TESTING__MONGO__HOST")
    port: int = Field(..., env="TESTING__MONGO__PORT")
    username: Optional[str] = Field(None, env="TESTING__MONGO__USERNAME")
    password: Optional[str] = Field(None, env="TESTING__MONGO__PASSWORD")
    database: str = Field(..., env="TESTING__MONGO__DATABASE")
    
    @property
    def url(self):
        if self.username and self.password:
            return f"mongodb://{self.username}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"
        return f"mongodb://{self.host}:{self.port}/{self.database}"

class TestConfig(BaseModel):
    default_test_size: int = 10  # Количество вопросов в тесте
    question_pool_size: int = 15  # Общий пул вопросов для выборки
    max_attempts_per_day: int = 30  # Максимум попыток в день
    test_time_limit_minutes: int = 30  # Ограничение времени на тест

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="TESTING__",
        case_sensitive=False,
        extra='allow'
    )

    app_name: str = "Briolin Testing Service"
    service_name: str = "testing-service"
    debug: bool = Field(..., env="TESTING__DEBUG")
    version: str = "1.0.0"

    db: DatabaseConfig = Field(...)
    mongo: MongoDBConfig = Field(...)
    test_config: TestConfig = Field(default_factory=TestConfig)
    
    @property
    def rabbitmq(self) -> RabbitMQConfig:
        return get_shared_config().rabbitmq

settings = Settings()