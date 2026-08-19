from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ProfileQuestionsCreate(BaseModel):
    """Схема данных для сохранения ответов пользователя на вопросы профиля."""
    question_1: str = Field(..., min_length=10, max_length=500, description='Ответ пользователя на первый вопрос профиля')
    question_2: str = Field(..., min_length=10, max_length=500, description='Ответ пользователя на второй вопрос профиля')
    question_3: str = Field(..., min_length=10, max_length=500, description='Ответ пользователя на третий вопрос профиля')
    question_4: str = Field(..., min_length=10, max_length=500, description='Ответ пользователя на четвёртый вопрос профиля')
    question_5: str = Field(..., min_length=10, max_length=500, description='Ответ пользователя на пятый вопрос профиля')


class ProfileQuestionsUpdate(BaseModel):
    """Схема данных для частичного обновления ответов на вопросы профиля."""
    question_1: Optional[str] = Field(None, min_length=10, max_length=500, description='Новое значение ответа на первый вопрос профиля')
    question_2: Optional[str] = Field(None, min_length=10, max_length=500, description='Новое значение ответа на второй вопрос профиля')
    question_3: Optional[str] = Field(None, min_length=10, max_length=500, description='Новое значение ответа на третий вопрос профиля')
    question_4: Optional[str] = Field(None, min_length=10, max_length=500, description='Новое значение ответа на четвёртый вопрос профиля')
    question_5: Optional[str] = Field(None, min_length=10, max_length=500, description='Новое значение ответа на пятый вопрос профиля')


class ProfileQuestionsResponse(BaseModel):
    """Схема ответа с сохранёнными ответами пользователя на вопросы профиля."""
    model_config = ConfigDict(from_attributes=True)
    
    question_1: str = Field(..., description='Ответ пользователя на первый вопрос профиля')
    question_2: str = Field(..., description='Ответ пользователя на второй вопрос профиля')
    question_3: str = Field(..., description='Ответ пользователя на третий вопрос профиля')
    question_4: str = Field(..., description='Ответ пользователя на четвёртый вопрос профиля')
    question_5: str = Field(..., description='Ответ пользователя на пятый вопрос профиля')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления записи')