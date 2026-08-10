from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime

class QuestionAnswers(BaseModel):
    """Ответы на 5 вопросов"""
    question_1: str = Field(..., min_length=1, max_length=500, description='Ответ на первый вопрос, отправляемый вместе с лайком')
    question_2: str = Field(..., min_length=1, max_length=500, description='Ответ на второй вопрос, отправляемый вместе с лайком')
    question_3: str = Field(..., min_length=1, max_length=500, description='Ответ на третий вопрос, отправляемый вместе с лайком')
    question_4: str = Field(..., min_length=1, max_length=500, description='Ответ на четвёртый вопрос, отправляемый вместе с лайком')
    question_5: str = Field(..., min_length=1, max_length=500, description='Ответ на пятый вопрос, отправляемый вместе с лайком')


class LikeWithAnswersRequest(BaseModel):
    """Запрос на лайк с ответами на вопросы"""
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
    """Запрос на ответный лайк"""
    from_user_id: str = Field(..., description='Keycloak ID пользователя, отправившего лайк')
    answers: QuestionAnswers = Field(..., description='Ответы пользователя на вопросы')

class DeclineLikeRequest(BaseModel):
    """Запрос на отклонение лайка"""
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