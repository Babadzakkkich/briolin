from pydantic import BaseModel, Field
from typing import Optional, List
from .pagination import PaginationInfo


class ClassicSearchFilters(BaseModel):
    """Фильтры для классического поиска"""
    min_age: Optional[int] = Field(None, ge=18, le=100, description='Минимальный возраст пользователя для поиска')
    max_age: Optional[int] = Field(None, ge=18, le=100, description='Максимальный возраст пользователя для поиска')
    city: Optional[str] = Field(None, description='Город пользователя')


class TargetedSearchFilters(ClassicSearchFilters):
    """Фильтры для таргетированного поиска (без эмбеддингов)"""
    education: Optional[str] = Field(None, description='Информация об образовании пользователя')
    hobbies_keywords: Optional[List[str]] = Field(None, description='Ключевые слова для фильтрации по увлечениям')
    online_only: bool = Field(False, description='Признак поиска только среди пользователей, находящихся онлайн')


class SearchProfile(BaseModel):
    """Профиль в результатах поиска"""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    age: int = Field(..., description='Возраст пользователя')
    city: str = Field(..., description='Город пользователя')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')
    education: Optional[str] = Field(None, description='Информация об образовании пользователя')
    hobbies: Optional[str] = Field(None, description='Информация об увлечениях пользователя')


class SearchListResponse(BaseModel):
    """Ответ со списком найденных профилей и пагинацией"""
    profiles: List[SearchProfile] = Field(..., description='Список профилей пользователей')
    pagination: PaginationInfo = Field(..., description='Информация о пагинации результатов')