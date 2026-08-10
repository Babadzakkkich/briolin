from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from shared.schemas.shared import Gender
from .questions import ProfileQuestionsResponse


class BasicProfileCreate(BaseModel):
    """Схема данных для создания основной части профиля пользователя."""
    first_name: str = Field(..., min_length=1, max_length=100, description='Имя пользователя')
    last_name: str = Field(..., min_length=1, max_length=100, description='Фамилия пользователя')
    gender: Gender = Field(..., description='Пол пользователя')
    date_of_birth: date = Field(..., description='Дата рождения пользователя')
    city: str = Field(..., min_length=1, max_length=200, description='Город пользователя')


class BasicProfileResponse(BaseModel):
    """Схема ответа с основной информацией профиля пользователя."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description='Внутренний идентификатор профиля пользователя')
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    first_name: str = Field(..., description='Имя пользователя')
    last_name: str = Field(..., description='Фамилия пользователя')
    gender: Gender = Field(..., description='Пол пользователя')
    date_of_birth: date = Field(..., description='Дата рождения пользователя')
    city: str = Field(..., description='Город пользователя')
    online: bool = Field(..., description='Признак того, что пользователь находится онлайн')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')
    thumbnail_url: Optional[str] = Field(None, description='URL уменьшенной версии изображения аватара')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления записи')
    last_login_at: Optional[datetime] = Field(..., description='Дата и время последнего входа пользователя')


class BasicProfileUpdate(BaseModel):
    """Схема данных для частичного обновления основной информации профиля."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description='Имя пользователя')
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description='Фамилия пользователя')
    gender: Optional[Gender] = Field(None, description='Пол пользователя')
    date_of_birth: Optional[date] = Field(None, description='Дата рождения пользователя')
    city: Optional[str] = Field(None, min_length=1, max_length=200, description='Город пользователя')


class DetailedProfileCreate(BaseModel):
    """Схема данных для создания расширенной информации профиля пользователя."""
    about_me: str = Field(..., min_length=10, max_length=2000, description='Текстовое описание пользователя о себе')
    education: str = Field(..., min_length=1, max_length=500, description='Информация об образовании пользователя')
    hobbies: str = Field(..., min_length=1, max_length=1000, description='Информация об увлечениях пользователя')
    partner_preferences: str = Field(..., min_length=10, max_length=2000, description='Описание предпочтений пользователя к потенциальному партнёру')
    red_flags: Optional[List[str]] = Field(None, max_length=20, description='Список качеств или особенностей, которые пользователь не приемлет в партнёре')


class DetailedProfileResponse(BaseModel):
    """Схема ответа с расширенной информацией профиля пользователя."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description='Внутренний идентификатор расширенного профиля')
    about_me: str = Field(..., description='Текстовое описание пользователя о себе')
    education: str = Field(..., description='Информация об образовании пользователя')
    hobbies: str = Field(..., description='Информация об увлечениях пользователя')
    partner_preferences: str = Field(..., description='Описание предпочтений пользователя к потенциальному партнёру')
    red_flags: Optional[List[str]] = Field(None, description='Список качеств или особенностей, которые пользователь не приемлет в партнёре')


class DetailedProfileUpdate(BaseModel):
    """Схема данных для частичного обновления расширенной информации профиля."""
    about_me: Optional[str] = Field(None, min_length=10, max_length=2000, description='Текстовое описание пользователя о себе')
    education: Optional[str] = Field(None, min_length=1, max_length=500, description='Информация об образовании пользователя')
    hobbies: Optional[str] = Field(None, min_length=1, max_length=1000, description='Информация об увлечениях пользователя')
    partner_preferences: Optional[str] = Field(None, min_length=10, max_length=2000, description='Описание предпочтений пользователя к потенциальному партнёру')
    red_flags: Optional[List[str]] = Field(None, max_length=20, description='Список качеств или особенностей, которые пользователь не приемлет в партнёре')


class FullProfileResponse(BaseModel):
    """Схема ответа с полной информацией профиля пользователя."""
    model_config = ConfigDict(from_attributes=True)
    
    basic: BasicProfileResponse = Field(..., description='Основные данные профиля пользователя')
    detailed: Optional[DetailedProfileResponse] = Field(None, description='Расширенные данные профиля пользователя')
    questions: Optional[ProfileQuestionsResponse] = Field(None, description='Список вопросов')


class FullProfileCreate(BaseModel):
    """Схема данных для комплексного создания полного профиля пользователя."""
    basic: BasicProfileCreate = Field(..., description='Основные данные профиля пользователя')
    detailed: DetailedProfileCreate = Field(..., description='Расширенные данные профиля пользователя')


class FullProfileUpdate(BaseModel):
    """Схема данных для комплексного обновления полного профиля пользователя."""
    basic: Optional[BasicProfileUpdate] = Field(None, description='Основные данные профиля пользователя')
    detailed: Optional[DetailedProfileUpdate] = Field(None, description='Расширенные данные профиля пользователя')