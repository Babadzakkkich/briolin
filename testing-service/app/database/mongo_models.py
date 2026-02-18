from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    LIKERT_SCALE = "likert_scale"
    TRUE_FALSE = "true_false"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class AnswerOption(BaseModel):
    id: str = Field(..., description="Уникальный ID варианта ответа")
    text: str = Field(..., description="Текст варианта ответа")
    score: float = Field(..., description="Количество баллов за этот ответ")
    is_correct: Optional[bool] = Field(None, description="Правильный ли ответ")

class Question(BaseModel):
    id: str = Field(..., description="Уникальный ID вопроса")
    text: str = Field(..., description="Текст вопроса")
    question_type: QuestionType = Field(...)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    category: str = Field(...)
    tags: List[str] = Field(default_factory=list)
    
    options: List[AnswerOption] = Field(default_factory=list)
    min_value: Optional[int] = Field(default=1)
    max_value: Optional[int] = Field(default=5)
    labels: Optional[Dict[str, str]] = Field(default=None)
    
    explanation: Optional[str] = Field(None, description="Пояснение к ответу")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TestTemplate(BaseModel):
    id: str = Field(..., description="Уникальный ID шаблона")
    name: str = Field(..., description="Название теста")
    description: str = Field(...)
    version: str = Field(default="1.0.0")
    
    question_count: int = Field(default=10, ge=1, le=50)
    time_limit_minutes: int = Field(default=30, ge=5, le=180)
    pass_threshold: float = Field(default=70.0, ge=0, le=100)
    
    question_pool: List[str] = Field(default_factory=list)
    sampling_strategy: str = Field(default="random")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)