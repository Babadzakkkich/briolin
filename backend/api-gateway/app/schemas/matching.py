from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from shared.schemas.shared import Gender

# ========== LIKE/DISLIKE SCHEMAS ==========

class LikeRequest(BaseModel):
    """Запрос на лайк"""
    target_user_id: str = Field(..., description="Keycloak ID пользователя, которого лайкаем")


class DislikeRequest(BaseModel):
    """Запрос на дизлайк"""
    target_user_id: str = Field(..., description="Keycloak ID пользователя, которого дизлайкаем")


class LikeUsageInfo(BaseModel):
    """Информация об использовании лайков"""
    likes_used_today: int = Field(..., description="Использовано лайков сегодня")
    daily_like_limit: int = Field(..., description="Дневной лимит лайков")
    likes_remaining: int = Field(..., description="Осталось лайков на сегодня")


# ========== SWIPE SCHEMAS (для обратной совместимости) ==========

class SwipeResponse(BaseModel):
    """Ответ на свайп/лайк/дизлайк"""
    match: bool = Field(..., description="Произошёл ли взаимный мэтч")
    match_id: Optional[int] = Field(None, description="ID мэтча если match=true")
    chat_id: Optional[str] = Field(None, description="ID чата если match=true")


class SwipeStatusResponse(BaseModel):
    """Статус свайпа к конкретному пользователю"""
    swiped: bool = Field(..., description="Был ли совершён свайп")
    type: Optional[str] = Field(None, description="Тип свайпа: like или dislike")


# ========== MATCH SCHEMAS ==========

class MatchPartnerInfo(BaseModel):
    """Информация о партнёре по мэтчу"""
    keycloak_id: str = Field(..., description="Keycloak ID партнёра")
    display_name: str = Field(..., description="Отображаемое имя партнёра")
    avatar_url: Optional[str] = Field(None, description="URL аватарки партнёра")


class MatchResponse(BaseModel):
    """Ответ с информацией о мэтче"""
    model_config = ConfigDict(from_attributes=True)

    match_id: int = Field(..., description="ID мэтча")
    partner: MatchPartnerInfo = Field(..., description="Информация о партнёре")
    matched_at: datetime = Field(..., description="Дата и время создания мэтча")


# ========== PAGINATION SCHEMAS ==========

class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int = Field(1, description="Текущая страница")
    total_pages: int = Field(1, description="Всего страниц")
    total_results: int = Field(0, description="Всего результатов")
    page_size: int = Field(10, description="Размер страницы")


# ========== LOCK SCHEMAS ==========

class TargetedSearchLockInfo(BaseModel):
    """Информация о блокировке таргетированных рекомендаций (эмбеддинги)"""
    is_locked: bool = Field(..., description="Заблокирован ли пользователь")
    profiles_viewed: int = Field(..., description="Просмотрено профилей в текущем периоде")
    daily_limit: int = Field(..., description="Дневной лимит просмотров")
    locked_until: Optional[datetime] = Field(None, description="Время разблокировки")
    time_until_unlock: Optional[int] = Field(None, description="Секунд до разблокировки")


# ========== SEARCH SCHEMAS ==========

class ClassicSearchFilters(BaseModel):
    """Фильтры для классического поиска"""
    gender: Optional[Gender] = Field(None, description="Пол для фильтрации")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Минимальный возраст")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Максимальный возраст")
    city: Optional[str] = Field(None, min_length=1, max_length=200, description="Город")


class TargetedSearchFilters(ClassicSearchFilters):
    """Фильтры для таргетированного поиска (без эмбеддингов)"""
    education: Optional[str] = Field(None, min_length=1, max_length=500, description="Образование")
    hobbies_keywords: Optional[List[str]] = Field(None, max_length=10, description="Ключевые слова интересов")
    online_only: bool = Field(False, description="Только онлайн пользователи")


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


# ========== RECOMMENDATION SCHEMAS (ЭМБЕДДИНГИ) ==========

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
    about_me: Optional[str] = Field(None, description="О себе")
    hobbies: Optional[str] = Field(None, description="Хобби")
    red_flags: Optional[List[str]] = Field(None, description="Red flags")
    partner_preferences: Optional[str] = Field(None, description="Предпочтения партнёра")
    similarity: Optional[float] = Field(None, description="Степень семантической схожести (0-1)")
    combined_score: Optional[float] = Field(None, description="Комбинированный скор (similarity + близость по возрасту)")


class RecommendationListResponse(BaseModel):
    """Ответ со списком рекомендаций и пагинацией"""
    profiles: List[RecommendationProfile]
    pagination: PaginationInfo
    lock_info: Optional[TargetedSearchLockInfo] = None
    applied_filters: dict = Field(...)
    sentiment_boost_applied: bool = Field(False, description="Был ли применён тональный ре-ранкинг")

class QuestionAnswers(BaseModel):
    """Ответы на 5 вопросов"""
    question_1: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 1")
    question_2: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 2")
    question_3: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 3")
    question_4: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 4")
    question_5: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 5")


class LikeWithAnswersRequest(BaseModel):
    target_user_id: str = Field(..., description="Keycloak ID пользователя")
    answers: QuestionAnswers = Field(..., description="Ответы на 5 вопросов")

class LikeWithAnswersResponse(BaseModel):
    """Ответ на лайк с вопросами"""
    status: str = Field(..., description="liked или matched")
    message: str
    match_id: Optional[int] = None
    show_answers: bool = False
    answers: Optional[Dict[str, Any]] = None


class PendingLikeInfo(BaseModel):
    """Расширенная информация о входящем лайке"""
    from_user_id: str
    from_user_display_name: str
    from_user_age: int = Field(0, description="Возраст пользователя")
    from_user_city: str = Field("", description="Город пользователя")
    from_user_avatar: Optional[str] = None
    from_user_about_me: str = Field("", description="О себе")
    from_user_hobbies: str = Field("", description="Хобби")
    from_user_red_flags: List[str] = Field(default_factory=list, description="Red flags")
    from_user_partner_preferences: str = Field("", description="Предпочтения партнёра")
    answers: Dict[str, str]
    questions: Optional[Dict[str, str]] = None
    created_at: datetime

class ReverseLikeRequest(BaseModel):
    from_user_id: str = Field(..., description="ID пользователя, который лайкнул первым")
    answers: QuestionAnswers = Field(..., description="Ответы на его вопросы")

class DeclineLikeRequest(BaseModel):
    from_user_id: str = Field(..., description="ID пользователя, чей лайк отклонить")

class MatchAnswersResponse(BaseModel):
    """мэтч с ответами"""
    match_id: int
    partner: Dict[str, Any]
    matched_at: datetime
    my_answers: Dict[str, str]
    my_questions: Optional[Dict[str, str]] = None
    partner_answers: Dict[str, str]
    partner_questions: Optional[Dict[str, str]] = None


# ========== ADMIN SCHEMAS ==========

class ResetUserDataResponse(BaseModel):
    """Ответ на сброс данных пользователя"""
    message: str = Field(..., description="Сообщение о результате операции")
    swipes_deleted: int = Field(..., description="Количество удалённых свайпов")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str = Field(..., description="Описание ошибки")


class LikeLimitErrorResponse(BaseModel):
    """Ответ при превышении лимита лайков"""
    message: str = Field(..., description="Сообщение об ошибке")
    likes_used: int = Field(..., description="Использовано лайков")
    daily_limit: int = Field(..., description="Дневной лимит")


class TargetedSearchLockedErrorResponse(BaseModel):
    """Ответ при блокировке таргетированных рекомендаций"""
    message: str = Field(..., description="Сообщение об ошибке")
    unlock_time: Optional[str] = Field(None, description="Время разблокировки (ISO)")
    time_until_unlock: Optional[int] = Field(None, description="Секунд до разблокировки")
    profiles_viewed: int = Field(..., description="Просмотрено профилей")
    daily_limit: int = Field(..., description="Дневной лимит просмотров")
