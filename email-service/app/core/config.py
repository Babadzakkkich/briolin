from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from shared.config import get_shared_config, RabbitMQConfig


class SmtpConfig(BaseSettings):
    """SMTP настройки"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="EMAIL__SMTP__",
        case_sensitive=False,
        extra="ignore",
    )
    
    host: str = "smtp.gmail.com"
    port: int = 587
    user: str = ""  # Значение по умолчанию
    password: str = ""  # Значение по умолчанию
    from_email: Optional[str] = None
    use_tls: bool = True


class EmailServiceConfig(BaseSettings):
    """Основные настройки email-сервиса"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="EMAIL__",
        case_sensitive=False,
        extra="ignore",
    )
    
    debug: bool = True
    service_name: str = "email-service"
    queue_name: str = "email.notifications"


class Settings:
    """
    Композитная конфигурация email-сервиса.
    """
    
    def __init__(self):
        self.service = EmailServiceConfig()
        self.smtp = SmtpConfig()
    
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
    def queue_name(self) -> str:
        return self.service.queue_name
    
    @property
    def smtp_host(self) -> str:
        return self.smtp.host
    
    @property
    def smtp_port(self) -> int:
        return self.smtp.port
    
    @property
    def smtp_user(self) -> str:
        return self.smtp.user
    
    @property
    def smtp_password(self) -> str:
        return self.smtp.password
    
    @property
    def from_email(self) -> str:
        """Получить email отправителя"""
        if self.smtp.from_email:
            return self.smtp.from_email
        return self.smtp.user
    
    @property
    def use_tls(self) -> bool:
        return self.smtp.use_tls
    
    @property
    def app_name(self) -> str:
        return "Briolin Email Service"


settings = Settings()