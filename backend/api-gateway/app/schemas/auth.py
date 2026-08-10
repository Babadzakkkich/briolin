from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserRegister(BaseModel):
    """Схема данных для регистрации нового пользователя."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    username: str = Field(..., min_length=3, max_length=50, description='Имя пользователя для отображения и входа в систему')
    password: str = Field(..., min_length=6, description='Пароль пользователя')


class UserLogin(BaseModel):
    """Схема учётных данных для входа пользователя в систему."""
    username: str = Field(..., description='Имя пользователя для отображения и входа в систему')
    password: str = Field(..., description='Пароль пользователя')


class TokenResponse(BaseModel):
    """Внутренний ответ auth-service. Наружу браузеру токены не отдаём."""
    access_token: str = Field(..., description='Токен доступа для авторизации запросов')
    refresh_token: str = Field(..., description='Refresh-токен для обновления сессии пользователя')
    token_type: str = Field(..., description='Тип токена авторизации')
    expires_in: int = Field(..., description='Оставшееся время действия токена в секундах')
    refresh_expires_in: int = Field(..., description='Оставшееся время действия refresh-токена в секундах')


class SessionResponse(BaseModel):
    """Схема ответа с состоянием текущей пользовательской сессии."""
    authenticated: bool = Field(..., description='Признак успешной аутентификации пользователя')
    token_type: str = Field('Bearer', description='Тип токена авторизации')
    expires_in: int = Field(..., description='Оставшееся время действия токена в секундах')


class RefreshRequest(BaseModel):
    """Схема запроса на обновление токенов пользовательской сессии."""
    refresh_token: str = Field(..., description='Refresh-токен для обновления сессии пользователя')


class LogoutRequest(BaseModel):
    """Схема запроса на завершение пользовательской сессии."""
    refresh_token: str = Field(..., description='Refresh-токен для обновления сессии пользователя')


class UserResponse(BaseModel):
    """Схема ответа с основными данными учётной записи пользователя."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description='Внутренний идентификатор пользователя')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    is_active: bool = Field(..., description='Признак активности учётной записи')
