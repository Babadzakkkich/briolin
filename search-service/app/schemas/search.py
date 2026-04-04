from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, validator


class SearchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gender: Optional[str] = Field(None, description="Пол для фильтрации")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Минимальный возраст")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Максимальный возраст")
    city: Optional[str] = Field(None, description="Город для фильтрации")
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(10, ge=1, le=50, description="Размер страницы")

    @validator('min_age')
    def validate_min_age(cls, v):
        if v is not None and v < 18:
            raise ValueError('Minimum age must be at least 18')
        return v

    @validator('max_age')
    def validate_max_age(cls, v):
        if v is not None and v > 100:
            raise ValueError('Maximum age must be at most 100')
        return v


class TargetedSearchRequest(SearchRequest):
    """Расширенный запрос для таргетированного поиска"""
    model_config = ConfigDict(from_attributes=True)

    education: Optional[str] = Field(None, description="Образование для фильтрации")
    hobbies_keywords: Optional[List[str]] = Field(None, description="Ключевые слова для поиска по интересам")
    partner_preferences: Optional[str] = Field(None, description="Предпочтения в партнере")
    online_only: Optional[bool] = Field(False, description="Только онлайн пользователи")


class ProfilePreviewResponse(BaseModel):
    """Краткая информация о профиле для результатов поиска"""
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name: str
    gender: str
    age: int
    city: str
    online: bool
    education: Optional[str] = None
    hobbies: Optional[str] = None
    about_me: Optional[str] = None
    partner_preferences: Optional[str] = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    search_session_id: int
    profiles: List[ProfilePreviewResponse] = []
    filters: Dict[str, Any]
    created_at: datetime
    current_page: int = 1
    total_pages: int = 1
    total_results: int = 0
    has_next: bool = False
    has_previous: bool = False
    locked_until: Optional[datetime] = None
    time_until_unlock: Optional[int] = None
    profiles_viewed: int = 0


class SearchSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    search_session_id: int
    search_type: str
    filters: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_results: int = 0
    current_page: int = 1
    total_pages: int = 1
    user_id: int = Field(..., description="ID пользователя, которому принадлежит сессия")


class SearchLockInfoResponse(BaseModel):
    """Информация о блокировке поиска"""
    model_config = ConfigDict(from_attributes=True)

    search_type: str
    is_locked: bool
    profiles_viewed: int
    locked_until: Optional[datetime] = None
    time_until_unlock: Optional[int] = None


class ErrorResponse(BaseModel):
    detail: str