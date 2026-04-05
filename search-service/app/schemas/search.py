from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shared.schemas.shared import Gender


# ========== REQUEST SCHEMAS ==========

class SearchRequest(BaseModel):
    """Базовый запрос для поиска (без пагинации)"""
    model_config = ConfigDict(from_attributes=True)

    gender: Optional[Gender] = Field(None, description="Пол для фильтрации")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Минимальный возраст")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Максимальный возраст")
    city: Optional[str] = Field(None, min_length=1, max_length=200, description="Город")

    @field_validator('max_age')
    @classmethod
    def validate_age_range(cls, v, info):
        if v is not None:
            min_age = info.data.get('min_age')
            if min_age is not None and min_age > v:
                raise ValueError('min_age cannot be greater than max_age')
        return v


class SearchWithPaginationRequest(SearchRequest):
    """Запрос поиска с пагинацией (для API)"""
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(10, ge=1, le=50, description="Размер страницы")
    
    # НОВОЕ ПОЛЕ: список пользователей, которых нужно исключить из результатов
    exclude_user_ids: Optional[List[str]] = Field(
        None, 
        max_length=500,
        description="Список Keycloak ID пользователей, которых нужно исключить из результатов"
    )


class TargetedSearchRequest(SearchRequest):
    """Расширенный запрос для таргетированного поиска (без пагинации)"""
    
    education: Optional[str] = Field(None, min_length=1, max_length=500, description="Образование")
    hobbies_keywords: Optional[List[str]] = Field(None, max_length=10, description="Ключевые слова интересов")
    partner_preferences: Optional[str] = Field(None, min_length=1, max_length=2000, description="Предпочтения")
    online_only: bool = Field(False, description="Только онлайн пользователи")


class TargetedSearchWithPaginationRequest(TargetedSearchRequest):
    """Запрос таргетированного поиска с пагинацией (для API)"""
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(10, ge=1, le=50, description="Размер страницы")
    
    # НОВОЕ ПОЛЕ: список пользователей, которых нужно исключить из результатов
    exclude_user_ids: Optional[List[str]] = Field(
        None,
        max_length=500,
        description="Список Keycloak ID пользователей, которых нужно исключить из результатов"
    )


# ========== RESPONSE SCHEMAS ==========

class ProfilePreviewResponse(BaseModel):
    """Краткая информация о профиле для результатов поиска"""
    model_config = ConfigDict(from_attributes=True)
    
    keycloak_id: str = Field(..., description="Keycloak ID пользователя")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    gender: Gender
    age: int = Field(..., ge=18, le=100)
    city: str
    online: bool
    avatar_thumbnail_url: Optional[str] = Field(None, description="URL миниатюры аватарки")
    
    # Дополнительные поля для таргетированного поиска
    education: Optional[str] = None
    hobbies: Optional[str] = None
    about_me: Optional[str] = None
    partner_preferences: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Полное имя для отображения"""
        return f"{self.first_name} {self.last_name}"


class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int = 1
    total_pages: int = 1
    total_results: int = 0
    page_size: int = 10
    
    @property
    def has_next(self) -> bool:
        return self.current_page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        return self.current_page > 1


class SearchLockInfo(BaseModel):
    """Информация о блокировке таргетированного поиска"""
    is_locked: bool
    profiles_viewed: int
    locked_until: Optional[datetime] = None
    time_until_unlock: Optional[int] = Field(None, description="Секунд до разблокировки")


class SearchResponse(BaseModel):
    """Ответ на поисковый запрос"""
    model_config = ConfigDict(from_attributes=True)
    
    search_session_id: int
    profiles: List[ProfilePreviewResponse] = []
    filters: Dict[str, Any]
    created_at: datetime
    pagination: PaginationInfo
    lock_info: Optional[SearchLockInfo] = None


class SearchSessionInfo(BaseModel):
    """Информация о сохраненной поисковой сессии (без результатов)"""
    model_config = ConfigDict(from_attributes=True)
    
    search_session_id: int
    search_type: str
    filters: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_results: int = 0
    profiles_viewed: int = 0
    profiles_remaining: int = 0


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой"""
    detail: str
    code: Optional[str] = Field(None, description="Код ошибки для клиентской обработки")