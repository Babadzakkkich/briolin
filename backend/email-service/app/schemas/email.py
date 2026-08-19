from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from enum import Enum


class EmailType(str, Enum):
    WELCOME = "welcome"
    LOGIN = "login"
    TEST_COMPLETE = "test_complete"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_CONFIRMATION = "password_reset_confirmation"


class EmailSendRequest(BaseModel):
    """Схема запроса на отправку одного электронного письма."""
    to: EmailStr = Field(..., description='Адрес электронной почты получателя')
    subject: str = Field(..., description='Тема электронного письма')
    body: str = Field(..., description='Текстовое содержимое электронного письма')
    html_body: Optional[str] = Field(None, description='HTML-содержимое электронного письма')


class EmailTemplate(BaseModel):
    """Схема запроса на отправку электронного письма по заданному шаблону."""
    to: EmailStr = Field(..., description='Адрес электронной почты получателя')
    template: EmailType = Field(..., description='Тип шаблона электронного письма')
    context: Dict[str, Any] = Field(default_factory=dict, description='Контекст с данными для подстановки в шаблон письма')


class BulkEmailRequest(BaseModel):
    """Схема запроса на массовую отправку электронного письма нескольким получателям."""
    recipients: list[EmailStr] = Field(..., description='Список адресов электронной почты получателей')
    subject: str = Field(..., description='Тема электронного письма')
    body: str = Field(..., description='Текстовое содержимое электронного письма')
    html_body: Optional[str] = Field(None, description='HTML-содержимое электронного письма')


class EmailResponse(BaseModel):
    """Схема результата операции отправки электронного письма."""
    success: bool = Field(..., description='Признак успешного выполнения операции')
    message: str = Field(..., description='Сообщение о результате отправки письма')
    to: EmailStr = Field(..., description='Адрес электронной почты получателя')


class EmailNotification(BaseModel):
    """Схема данных уведомления, используемого для формирования электронного письма."""
    type: EmailType = Field(..., description='Тип почтового уведомления')
    to: EmailStr = Field(..., description='Адрес электронной почты получателя')
    name: Optional[str] = Field(None, description='Имя получателя уведомления')
    timestamp: Optional[str] = Field(None, description='Дата и время события, связанного с уведомлением')
    test_name: Optional[str] = Field(None, description='Название теста, связанного с уведомлением')
    score: Optional[int] = Field(None, description='Количество набранных баллов')
    total: Optional[int] = Field(None, description='Максимально возможное количество баллов')
    percentage: Optional[float] = Field(None, description='Результат теста в процентах')
    code: Optional[str] = Field(None, description='Код подтверждения')