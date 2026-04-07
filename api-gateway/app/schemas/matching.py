from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from shared.schemas.shared import Gender


# ========== SWIPE SCHEMAS ==========

class SwipeRequest(BaseModel):
    """Запрос на свайп (лайк/дизлайк)"""
    target_user_id: str = Field(..., description="Keycloak ID пользователя, на которого свайпаем")
    action: str = Field(..., pattern="^(like|dislike)$", description="Действие: like или dislike")


class SwipeResponse(BaseModel):
    """Ответ на свайп"""
    match: bool = Field(..., description="Произошёл ли взаимный матч")
    match_id: Optional[int] = Field(None, description="ID матча если match=true")
    chat_id: Optional[str] = Field(None, description="ID чата если match=true")


class SwipeStatusResponse(BaseModel):
    """Статус свайпа к конкретному пользователю"""
    swiped: bool = Field(..., description="Был ли совершён свайп")
    type: Optional[str] = Field(None, description="Тип свайпа: like или dislike")


# ========== MATCH SCHEMAS ==========

class MatchPartnerInfo(BaseModel):
    """Информация о партнёре по матчу"""
    keycloak_id: str = Field(..., description="Keycloak ID партнёра")
    display_name: str = Field(..., description="Отображаемое имя партнёра")
    avatar_url: Optional[str] = Field(None, description="URL аватарки партнёра")


class MatchResponse(BaseModel):
    """Ответ с информацией о матче"""
    model_config = ConfigDict(from_attributes=True)
    
    match_id: int = Field(..., description="ID матча")
    partner: MatchPartnerInfo = Field(..., description="Информация о партнёре")
    matched_at: datetime = Field(..., description="Дата и время создания матча")


# ========== PAGINATION SCHEMAS ==========

class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int = Field(1, description="Текущая страница")
    total_pages: int = Field(1, description="Всего страниц")
    total_results: int = Field(0, description="Всего результатов")
    page_size: int = Field(10, description="Размер страницы")


# ========== LOCK SCHEMAS ==========

class TargetedSearchLockInfo(BaseModel):
    """Информация о блокировке таргетированных рекомендаций"""
    is_locked: bool = Field(..., description="Заблокирован ли пользователь")
    profiles_viewed: int = Field(..., description="Просмотрено профилей в текущем периоде")
    daily_limit: int = Field(..., description="Дневной лимит просмотров")
    locked_until: Optional[datetime] = Field(None, description="Время разблокировки")
    time_until_unlock: Optional[int] = Field(None, description="Секунд до разблокировки")


# ========== RECOMMENDATION SCHEMAS ==========

class ClassicRecommendationFilters(BaseModel):
    """Фильтры для классического поиска рекомендаций"""
    gender: Optional[Gender] = Field(None, description="Пол для фильтрации")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Минимальный возраст")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Максимальный возраст")
    city: Optional[str] = Field(None, min_length=1, max_length=200, description="Город")


class TargetedRecommendationFilters(ClassicRecommendationFilters):
    """Фильтры для таргетированного (премиум) поиска рекомендаций"""
    education: Optional[str] = Field(None, min_length=1, max_length=500, description="Образование")
    hobbies_keywords: Optional[List[str]] = Field(None, max_length=10, description="Ключевые слова интересов")
    online_only: bool = Field(False, description="Только онлайн пользователи")


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


# ========== ADMIN SCHEMAS ==========

class ResetUserDataResponse(BaseModel):
    """Ответ на сброс данных пользователя"""
    message: str = Field(..., description="Сообщение о результате операции")
    swipes_deleted: int = Field(..., description="Количество удалённых свайпов")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str = Field(..., description="Описание ошибки")