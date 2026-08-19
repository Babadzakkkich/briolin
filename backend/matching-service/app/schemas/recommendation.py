from pydantic import BaseModel, Field
from typing import Optional, List
from .pagination import PaginationInfo
from .lock import TargetedSearchLockInfo


class TargetedRecommendationFilters(BaseModel):
    """
    Фильтры для таргетированных рекомендаций (эмбеддинги).
    Все поля опциональны - если не указаны, определяются автоматически.
    """
    city: Optional[str] = Field(None, min_length=1, max_length=200, description='Город пользователя')


class RecommendationProfile(BaseModel):
    """Профиль в результатах рекомендаций по эмбеддингам"""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    age: int = Field(..., description='Возраст пользователя')
    city: str = Field(..., description='Город пользователя')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')
    similarity: Optional[float] = Field(None, description='Степень сходства профилей в диапазоне от 0 до 1')
    combined_score: Optional[float] = Field(None, description='Итоговая оценка релевантности рекомендации')
    about_me: Optional[str] = Field(None, description='Текстовое описание пользователя о себе')
    hobbies: Optional[str] = Field(None, description='Информация об увлечениях пользователя')
    red_flags: Optional[List[str]] = Field(None, description='Список качеств или особенностей, которые пользователь не приемлет в партнёре')
    partner_preferences: Optional[str] = Field(None, description='Описание предпочтений пользователя к потенциальному партнёру')


class RecommendationListResponse(BaseModel):
    """Ответ со списком рекомендаций и пагинацией"""
    profiles: List[RecommendationProfile] = Field(..., description='Список профилей пользователей')
    pagination: PaginationInfo = Field(..., description='Информация о пагинации результатов')
    lock_info: Optional[TargetedSearchLockInfo] = Field(None, description='Информация о текущей блокировке таргетированного поиска')
    applied_filters: dict = Field(..., description='Фильтры, применённые при формировании результатов')
    sentiment_boost_applied: bool = Field(False, description='Признак применения повторного ранжирования с учётом тональности')