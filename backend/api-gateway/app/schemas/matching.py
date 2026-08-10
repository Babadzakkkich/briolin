from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, List
from datetime import datetime


# ========== LIKE/DISLIKE SCHEMAS ==========

class LikeRequest(BaseModel):
    """Запрос на лайк"""
    target_user_id: str = Field(..., description='Keycloak ID пользователя, к которому относится действие')


class DislikeRequest(BaseModel):
    """Запрос на дизлайк"""
    target_user_id: str = Field(..., description='Keycloak ID пользователя, к которому относится действие')


class LikeUsageInfo(BaseModel):
    """Информация об использовании лайков"""
    likes_used_today: int = Field(..., description='Количество лайков, использованных за текущие сутки')
    daily_like_limit: int = Field(..., description='Суточный лимит лайков')
    likes_remaining: int = Field(..., description='Количество лайков, оставшихся до суточного лимита')


# ========== SWIPE SCHEMAS (для обратной совместимости) ==========

class SwipeResponse(BaseModel):
    """Ответ на свайп/лайк/дизлайк"""
    match: bool = Field(..., description='Признак возникновения взаимного совпадения пользователей')
    match_id: Optional[int] = Field(None, description='Уникальный идентификатор совпадения пользователей')
    chat_id: Optional[str] = Field(None, description='Идентификатор чата, созданного при взаимном совпадении')


class SwipeStatusResponse(BaseModel):
    """Статус свайпа к конкретному пользователю"""
    swiped: bool = Field(..., description='Признак наличия ранее выполненного свайпа для пользователя')
    type: Optional[str] = Field(None, description='Тип ранее выполненного свайпа')


# ========== MATCH SCHEMAS ==========

class MatchPartnerInfo(BaseModel):
    """Информация о партнёре по матчу"""
    keycloak_id: str = Field(..., description='Keycloak ID пользователя-партнёра')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')


class MatchResponse(BaseModel):
    """Ответ с информацией о матче"""
    model_config = ConfigDict(from_attributes=True)
    
    match_id: int = Field(..., description='Уникальный идентификатор совпадения пользователей')
    partner: MatchPartnerInfo = Field(..., description='Информация о пользователе, с которым возникло совпадение')
    matched_at: datetime = Field(..., description='Дата и время возникновения совпадения')


# ========== PAGINATION SCHEMAS ==========

class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int = Field(1, description='Номер текущей страницы')
    total_pages: int = Field(1, description='Общее количество страниц')
    total_results: int = Field(0, description='Общее количество найденных результатов')
    page_size: int = Field(10, description='Количество элементов на одной странице')


# ========== LOCK SCHEMAS ==========

class TargetedSearchLockInfo(BaseModel):
    """Информация о блокировке таргетированных рекомендаций (эмбеддинги)"""
    is_locked: bool = Field(..., description='Признак блокировки таргетированного поиска')
    profiles_viewed: int = Field(..., description='Количество просмотренных профилей')
    daily_limit: int = Field(..., description='Суточный лимит операций')
    locked_until: Optional[datetime] = Field(None, description='Дата и время окончания блокировки')
    time_until_unlock: Optional[int] = Field(None, description='Количество секунд до снятия блокировки')


# ========== SEARCH SCHEMAS ==========

class ClassicSearchFilters(BaseModel):
    """Фильтры для классического поиска"""
    min_age: Optional[int] = Field(None, ge=18, le=100, description='Минимальный возраст пользователя для поиска')
    max_age: Optional[int] = Field(None, ge=18, le=100, description='Максимальный возраст пользователя для поиска')
    city: Optional[str] = Field(None, min_length=1, max_length=200, description='Город пользователя')


class TargetedSearchFilters(ClassicSearchFilters):
    """Фильтры для таргетированного поиска (без эмбеддингов)"""
    education: Optional[str] = Field(None, min_length=1, max_length=500, description='Информация об образовании пользователя')
    hobbies_keywords: Optional[List[str]] = Field(None, max_length=10, description='Ключевые слова для фильтрации по увлечениям')
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


# ========== RECOMMENDATION SCHEMAS (ЭМБЕДДИНГИ) ==========

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
    about_me: Optional[str] = Field(None, description='Текстовое описание пользователя о себе')
    hobbies: Optional[str] = Field(None, description='Информация об увлечениях пользователя')
    red_flags: Optional[List[str]] = Field(None, description='Список качеств или особенностей, которые пользователь не приемлет в партнёре')
    partner_preferences: Optional[str] = Field(None, description='Описание предпочтений пользователя к потенциальному партнёру')
    similarity: Optional[float] = Field(None, description='Степень сходства профилей в диапазоне от 0 до 1')
    combined_score: Optional[float] = Field(None, description='Итоговая оценка релевантности рекомендации')


class RecommendationListResponse(BaseModel):
    """Ответ со списком рекомендаций и пагинацией"""
    profiles: List[RecommendationProfile] = Field(..., description='Список профилей пользователей')
    pagination: PaginationInfo = Field(..., description='Информация о пагинации результатов')
    lock_info: Optional[TargetedSearchLockInfo] = Field(None, description='Информация о текущей блокировке таргетированного поиска')
    applied_filters: dict = Field(..., description='Фильтры, применённые при формировании результатов')
    sentiment_boost_applied: bool = Field(False, description='Признак применения повторного ранжирования с учётом тональности')

class QuestionAnswers(BaseModel):
    """Ответы на 5 вопросов"""
    question_1: str = Field(..., min_length=1, max_length=500, description='Ответ на первый вопрос, отправляемый вместе с лайком')
    question_2: str = Field(..., min_length=1, max_length=500, description='Ответ на второй вопрос, отправляемый вместе с лайком')
    question_3: str = Field(..., min_length=1, max_length=500, description='Ответ на третий вопрос, отправляемый вместе с лайком')
    question_4: str = Field(..., min_length=1, max_length=500, description='Ответ на четвёртый вопрос, отправляемый вместе с лайком')
    question_5: str = Field(..., min_length=1, max_length=500, description='Ответ на пятый вопрос, отправляемый вместе с лайком')


class LikeWithAnswersRequest(BaseModel):
    """Схема запроса на отправку лайка пользователю вместе с ответами на вопросы."""
    target_user_id: str = Field(..., description='Keycloak ID пользователя, к которому относится действие')
    answers: QuestionAnswers = Field(..., description='Ответы пользователя на вопросы')

class LikeWithAnswersResponse(BaseModel):
    """Ответ на лайк с вопросами"""
    status: str = Field(..., description='Статус обработки лайка с ответами')
    message: str = Field(..., description='Сообщение о результате обработки лайка')
    match_id: Optional[int] = Field(None, description='Уникальный идентификатор совпадения пользователей')
    show_answers: bool = Field(False, description='Признак необходимости показать ответы после обработки лайка')
    answers: Optional[Dict[str, Any]] = Field(None, description='Ответы пользователя на вопросы')


class PendingLikeInfo(BaseModel):
    """Расширенная информация о входящем лайке"""
    from_user_id: str = Field(..., description='Keycloak ID пользователя, отправившего лайк')
    from_user_display_name: str = Field(..., description='Отображаемое имя пользователя, отправившего лайк')
    from_user_age: int = Field(0, description='Возраст пользователя, отправившего лайк')
    from_user_city: str = Field('', description='Город пользователя, отправившего лайк')
    from_user_avatar: Optional[str] = Field(None, description='URL аватара пользователя, отправившего лайк')
    from_user_about_me: str = Field('', description='Описание профиля пользователя, отправившего лайк')
    from_user_hobbies: str = Field('', description='Информация об увлечениях пользователя, отправившего лайк')
    from_user_red_flags: List[str] = Field(default_factory=list, description='Список неприемлемых качеств партнёра пользователя, отправившего лайк')
    from_user_partner_preferences: str = Field('', description='Предпочтения к партнёру пользователя, отправившего лайк')
    answers: Dict[str, str] = Field(..., description='Ответы пользователя на вопросы')
    questions: Optional[Dict[str, str]] = Field(None, description='Список вопросов')
    created_at: datetime = Field(..., description='Дата и время создания записи')

class ReverseLikeRequest(BaseModel):
    """Схема запроса на ответный лайк пользователю с передачей ответов на вопросы."""
    from_user_id: str = Field(..., description='Keycloak ID пользователя, отправившего лайк')
    answers: QuestionAnswers = Field(..., description='Ответы пользователя на вопросы')

class DeclineLikeRequest(BaseModel):
    """Схема запроса на отклонение входящего лайка от пользователя."""
    from_user_id: str = Field(..., description='Keycloak ID пользователя, отправившего лайк')

class MatchAnswersResponse(BaseModel):
    """Матч с ответами"""
    match_id: int = Field(..., description='Уникальный идентификатор совпадения пользователей')
    partner: Dict[str, Any] = Field(..., description='Информация о пользователе, с которым возникло совпадение')
    matched_at: datetime = Field(..., description='Дата и время возникновения совпадения')
    my_answers: Dict[str, str] = Field(..., description='Ответы текущего пользователя, связанные с совпадением')
    my_questions: Optional[Dict[str, str]] = Field(None, description='Вопросы текущего пользователя, связанные с совпадением')
    partner_answers: Dict[str, str] = Field(..., description='Ответы пользователя-партнёра, связанные с совпадением')
    partner_questions: Optional[Dict[str, str]] = Field(None, description='Вопросы пользователя-партнёра, связанные с совпадением')


# ========== ADMIN SCHEMAS ==========

class ResetUserDataResponse(BaseModel):
    """Ответ на сброс данных пользователя"""
    message: str = Field(..., description='Сообщение о результате сброса данных пользователя')
    swipes_deleted: int = Field(..., description='Количество удалённых свайпов пользователя')


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str = Field(..., description='Подробное описание ошибки')


class LikeLimitErrorResponse(BaseModel):
    """Ответ при превышении лимита лайков"""
    message: str = Field(..., description='Сообщение о превышении суточного лимита лайков')
    likes_used: int = Field(..., description='Количество использованных лайков')
    daily_limit: int = Field(..., description='Суточный лимит операций')


class TargetedSearchLockedErrorResponse(BaseModel):
    """Ответ при блокировке таргетированных рекомендаций"""
    message: str = Field(..., description='Сообщение о блокировке таргетированного поиска')
    unlock_time: Optional[str] = Field(None, description='Время снятия блокировки')
    time_until_unlock: Optional[int] = Field(None, description='Количество секунд до снятия блокировки')
    profiles_viewed: int = Field(..., description='Количество просмотренных профилей')
    daily_limit: int = Field(..., description='Суточный лимит операций')