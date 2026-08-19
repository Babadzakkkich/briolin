from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime
from shared.schemas.shared import UserRole

class UserProfileCreate(BaseModel):
    """Внутренняя схема данных для создания пользовательского профиля."""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    username: str = Field(..., min_length=3, max_length=50, description='Имя пользователя для отображения и входа в систему')
    role: UserRole = Field(..., description='Роль пользователя')

class UserProfileResponse(BaseModel):
    """Внутренняя схема ответа с данными пользовательского профиля."""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    username: str = Field(..., description='Имя пользователя для отображения и входа в систему')
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    roles: List[UserRole] = Field(..., description='Список ролей пользователя')
    is_active: bool = Field(..., description='Признак активности учётной записи')
    is_test_passed: bool = Field(..., description='Признак успешного прохождения обязательного тестирования')
    created_at: datetime = Field(..., description='Дата и время создания записи')