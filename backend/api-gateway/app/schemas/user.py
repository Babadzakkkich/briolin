from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, Any, Dict
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

class AsyncOperationResponse(BaseModel):
    """Схема ответа о запуске асинхронной операции, выполняемой через сагу."""
    status: str = Field(..., description='Статус запуска асинхронной операции')
    message: str = Field(..., description='Текст сообщения')
    saga_id: str = Field(..., description='Уникальный идентификатор saga-операции')
    check_status_url: str = Field(..., description='URL для проверки состояния асинхронной операции')

class SagaStepInfo(BaseModel):
    """Схема состояния отдельного шага распределённой операции саги."""
    name: str = Field(..., description='Название шага saga-операции')
    status: str = Field(..., description='Статус выполнения шага saga-операции')
    attempts: int = Field(..., description='Количество попыток выполнения шага')
    error: Optional[str] = Field(None, description='Описание ошибки')
    created_at: Optional[datetime] = Field(None, description='Дата и время создания записи')

class SagaStatusResponse(BaseModel):
    """Схема ответа с текущим состоянием и результатами выполнения саги."""
    saga_id: str = Field(..., description='Уникальный идентификатор saga-операции')
    name: str = Field(..., description='Название saga-операции')
    status: str = Field(..., description='Текущий статус saga-операции')
    created_at: Optional[datetime] = Field(None, description='Дата и время создания записи')
    updated_at: Optional[datetime] = Field(None, description='Дата и время последнего обновления записи')
    completed_at: Optional[datetime] = Field(None, description='Дата и время завершения операции')
    error: Optional[str] = Field(None, description='Описание ошибки')
    steps: List[SagaStepInfo] = Field([], description='Список шагов saga-операции')
    step_results: Optional[Dict[str, Any]] = Field(None, description='Результаты выполнения шагов saga-операции')
    user: Optional[Dict[str, Any]] = Field(None, description='Данные пользователя')
    profile: Optional[Dict[str, Any]] = Field(None, description='Данные профиля пользователя')