from pydantic import BaseModel, Field
from typing import Optional, List
from shared.schemas.shared import Gender
from .pagination import PaginationInfo


class ClassicSearchFilters(BaseModel):
    """Фильтры для классического поиска"""
    gender: Optional[Gender] = None
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    city: Optional[str] = None


class TargetedSearchFilters(ClassicSearchFilters):
    """Фильтры для таргетированного поиска (без эмбеддингов)"""
    education: Optional[str] = None
    hobbies_keywords: Optional[List[str]] = None
    online_only: bool = False


class SearchProfile(BaseModel):
    """Профиль в результатах поиска"""
    keycloak_id: str = Field(..., description="Keycloak ID пользователя")
    display_name: str = Field(..., description="Отображаемое имя")
    age: int = Field(..., description="Возраст")
    city: str = Field(..., description="Город")
    avatar_url: Optional[str] = Field(None, description="URL аватарки")
    education: Optional[str] = Field(None, description="Образование")
    hobbies: Optional[str] = Field(None, description="Интересы")


class SearchListResponse(BaseModel):
    """Ответ со списком найденных профилей и пагинацией"""
    profiles: List[SearchProfile] = Field(..., description="Список профилей")
    pagination: PaginationInfo = Field(..., description="Информация о пагинации")