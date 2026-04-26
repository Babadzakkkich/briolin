from pydantic import BaseModel, Field
from typing import Optional, List
from .pagination import PaginationInfo
from .lock import TargetedSearchLockInfo


class TargetedRecommendationFilters(BaseModel):
    """
    Фильтры для таргетированных рекомендаций (эмбеддинги).
    Все поля опциональны - если не указаны, определяются автоматически.
    """
    city: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200, 
        description="Город (если не указан - используется город пользователя)"
    )


class RecommendationProfile(BaseModel):
    """Профиль в результатах рекомендаций по эмбеддингам"""
    keycloak_id: str = Field(..., description="Keycloak ID пользователя")
    display_name: str = Field(..., description="Отображаемое имя")
    age: int = Field(..., description="Возраст")
    city: str = Field(..., description="Город")
    avatar_url: Optional[str] = Field(None, description="URL аватарки")
    similarity: Optional[float] = Field(None, description="Степень схожести (0-1)")
    combined_score: Optional[float] = Field(None, description="Комбинированный скор (similarity + близость по возрасту)")


class RecommendationListResponse(BaseModel):
    """Ответ со списком рекомендаций и пагинацией"""
    profiles: List[RecommendationProfile]
    pagination: PaginationInfo
    lock_info: Optional[TargetedSearchLockInfo] = None
    applied_filters: dict = Field(...)
    sentiment_boost_applied: bool = Field(False, description="Был ли применён тональный ре-ранкинг")