from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    gender: Optional[str] = Field(None, description="Пол для фильтрации")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Минимальный возраст")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Максимальный возраст")
    city: Optional[str] = Field(None, description="Город для фильтрации")
    page: int = Field(1, ge=1, description="Номер страницы")  # ДОБАВЛЕНО
    limit: int = Field(10, ge=1, le=50, description="Размер страницы")  # ДОБАВЛЕНО

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
    education: Optional[str] = Field(None, description="Образование для фильтрации")
    hobbies_keywords: Optional[List[str]] = Field(None, description="Ключевые слова для поиска по интересам")
    partner_preferences: Optional[str] = Field(None, description="Предпочтения в партнере")
    online_only: Optional[bool] = Field(False, description="Только онлайн пользователи")


class ProfilePreviewResponse(BaseModel):
    """Краткая информация о профиле для результатов поиска"""
    user_id: int
    keycloak_id: str
    first_name: str
    last_name: str
    gender: str
    age: int
    city: str
    online: bool
    last_login_at: Optional[datetime]
    # Для таргетированного поиска
    education: Optional[str] = None
    hobbies: Optional[str] = None
    about_me: Optional[str] = None
    partner_preferences: Optional[str] = None


class SearchResponse(BaseModel):
    search_session_id: int
    user_ids: List[int]
    profiles: List[ProfilePreviewResponse] = []  # ДОБАВЛЕНО
    filters: Dict[str, Any]
    created_at: datetime
    # ДОБАВЛЕННЫЕ ПОЛЯ
    current_page: int = 1
    total_pages: int = 1
    total_results: int = 0
    has_next: bool = False
    has_previous: bool = False
    locked_until: Optional[datetime] = None
    time_until_unlock: Optional[int] = None
    profiles_viewed: int = 0


class SearchSessionResponse(BaseModel):
    search_session_id: int
    search_type: str
    filters: Dict[str, Any]
    results: List[int]
    viewed_profiles: List[int] = []  # ДОБАВЛЕНО
    current_page: int = 1  # ДОБАВЛЕНО
    total_pages: int = 1  # ДОБАВЛЕНО
    total_results: int = 0  # ДОБАВЛЕНО
    created_at: datetime
    updated_at: Optional[datetime] = None  # ДОБАВЛЕНО


class SearchLockInfoResponse(BaseModel):  # НОВАЯ СХЕМА
    """Информация о блокировке поиска"""
    user_id: int
    search_type: str
    is_locked: bool
    profiles_viewed: int
    locked_until: Optional[datetime] = None
    time_until_unlock: Optional[int] = None  # секунды до разблокировки


class ErrorResponse(BaseModel):
    detail: str