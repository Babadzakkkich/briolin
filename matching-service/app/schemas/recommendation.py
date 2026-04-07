from pydantic import BaseModel, Field
from typing import Optional, List
from shared.schemas.shared import Gender
from .pagination import PaginationInfo
from .lock import TargetedSearchLockInfo


class ClassicRecommendationFilters(BaseModel):
    """Фильтры для классического поиска рекомендаций"""
    gender: Optional[Gender] = None
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    city: Optional[str] = None


class TargetedRecommendationFilters(ClassicRecommendationFilters):
    """Фильтры для таргетированного (премиум) поиска рекомендаций"""
    education: Optional[str] = None
    hobbies_keywords: Optional[List[str]] = None
    online_only: bool = False


class RecommendationProfile(BaseModel):
    """Профиль в результатах рекомендаций"""
    keycloak_id: str = Field(..., description="Keycloak ID пользователя")
    display_name: str = Field(..., description="Отображаемое имя")
    age: int = Field(..., description="Возраст")
    city: str = Field(..., description="Город")
    avatar_url: Optional[str] = Field(None, description="URL аватарки")
    similarity: Optional[float] = Field(None, description="Степень схожести (0-1, только для таргетированного поиска)")


class RecommendationListResponse(BaseModel):
    """Ответ со списком рекомендаций и пагинацией"""
    profiles: List[RecommendationProfile] = Field(..., description="Список профилей")
    pagination: PaginationInfo = Field(..., description="Информация о пагинации")
    lock_info: Optional[TargetedSearchLockInfo] = Field(None, description="Информация о блокировке (только для таргетированного поиска)")