from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime

class QuestionAnswers(BaseModel):
    """Ответы на 5 вопросов"""
    question_1: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 1")
    question_2: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 2")
    question_3: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 3")
    question_4: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 4")
    question_5: str = Field(..., min_length=1, max_length=500, description="Ответ на вопрос 5")


class LikeWithAnswersRequest(BaseModel):
    """Запрос на лайк с ответами на вопросы"""
    target_user_id: str = Field(..., description="Keycloak ID пользователя")
    answers: QuestionAnswers = Field(..., description="Ответы на 5 вопросов")


class LikeWithAnswersResponse(BaseModel):
    """Ответ на лайк с вопросами"""
    status: str = Field(..., description="liked или matched")
    message: str
    match_id: Optional[int] = None
    show_answers: bool = Field(False, description="Показывать ли ответы")
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
    """Запрос на ответный лайк"""
    from_user_id: str = Field(..., description="ID пользователя, который лайкнул первым")
    answers: QuestionAnswers = Field(..., description="Ответы на его вопросы")

class DeclineLikeRequest(BaseModel):
    """Запрос на отклонение лайка"""
    from_user_id: str = Field(..., description="ID пользователя, чей лайк отклонить")

class MatchAnswersResponse(BaseModel):
    """Матч с ответами"""
    match_id: int
    partner: Dict[str, Any]
    matched_at: datetime
    my_answers: Dict[str, str]
    my_questions: Optional[Dict[str, str]] = None
    partner_answers: Dict[str, str]
    partner_questions: Optional[Dict[str, str]] = None