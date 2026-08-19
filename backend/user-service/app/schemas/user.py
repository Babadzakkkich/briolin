from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from shared.schemas.shared import UserRole

class UserBase(BaseModel):
    """Базовая схема данных пользователя, общая для операций с учётной записью."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description='Имя пользователя для отображения и входа в систему')
    email: Optional[EmailStr] = Field(None, description='Адрес электронной почты пользователя')

class UserPublic(BaseModel):
    """Схема публичных данных пользователя, возвращаемых через API."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description='Внутренний идентификатор пользователя')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    username: str = Field(..., description='Имя пользователя для отображения и входа в систему')
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    is_active: bool = Field(..., description='Признак активности учётной записи')
    is_test_passed: bool = Field(..., description='Признак успешного прохождения обязательного тестирования')
    roles: List[UserRole] = Field(..., description='Список ролей пользователя')
    created_at: datetime = Field(..., description='Дата и время создания записи')

class UserList(BaseModel):
    """Схема ответа со списком пользователей и данными пагинации."""
    users: List[UserPublic] = Field(..., description='Список пользователей')
    total: int = Field(..., description='Общее количество элементов')
    page: int = Field(..., description='Номер страницы результатов')
    size: int = Field(..., description='Количество элементов на странице')

class UserRolesUpdate(BaseModel):
    """Схема запроса на изменение набора ролей пользователя."""
    roles: List[UserRole] = Field(..., description='Список ролей пользователя')

class UserMeResponse(BaseModel):
    """Схема ответа с данными текущего авторизованного пользователя."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description='Внутренний идентификатор текущего пользователя')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    username: str = Field(..., description='Имя пользователя для отображения и входа в систему')
    email: str = Field(..., description='Адрес электронной почты пользователя')
    roles: List[UserRole] = Field(..., description='Список ролей пользователя')
    is_active: bool = Field(..., description='Признак активности учётной записи')
    is_test_passed: bool = Field(..., description='Признак успешного прохождения обязательного тестирования')
    created_at: datetime = Field(..., description='Дата и время создания записи')