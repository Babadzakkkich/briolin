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

class PersonalityDimension(str, Enum):
    ROMANTIC = "romantic"
    ADVENTURER = "adventurer"
    INTELLECTUAL = "intellectual"
    CAREGIVER = "caregiver"
    LEADER = "leader"
    FREE_SPIRIT = "free_spirit"

class AnswerOption(BaseModel):
    """Вариант ответа на вопрос"""
    id: str = Field(..., description="Уникальный ID варианта ответа")
    text: str = Field(..., description="Текст варианта ответа")
    score_impact: Dict[PersonalityDimension, float] = Field(
        default_factory=dict,
        description="Влияние на баллы по типам личности"
    )
    is_correct: Optional[bool] = Field(None, description="Правильный ли ответ (если применимо)")

class Question(BaseModel):
    """Вопрос теста"""
    id: str = Field(..., description="Уникальный ID вопроса")
    text: str = Field(..., description="Текст вопроса")
    question_type: QuestionType = Field(..., description="Тип вопроса")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    category: str = Field(..., description="Категория вопроса")
    tags: List[str] = Field(default_factory=list)
    
    # Для разных типов вопросов
    options: List[AnswerOption] = Field(default_factory=list)  # Для MULTIPLE_CHOICE
    min_value: Optional[int] = Field(default=1)  # Для LIKERT_SCALE
    max_value: Optional[int] = Field(default=5)  # Для LIKERT_SCALE
    labels: Optional[Dict[str, str]] = Field(default=None)  # Подписи для шкалы
    
    # ИСПРАВЛЕНО: Добавлен default_factory и проверка на None
    personality_dimensions: List[PersonalityDimension] = Field(
        default_factory=list,
        description="Какие типы личности измеряет этот вопрос"
    )
    
    explanation: Optional[str] = Field(None, description="Пояснение к вопросу")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "q1",
                "text": "Как вы обычно проводите выходные?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "lifestyle",
                "tags": ["weekend", "hobbies"],
                "options": [
                    {
                        "id": "a1",
                        "text": "Читаю книги или смотрю фильмы дома",
                        "score_impact": {"intellectual": 2, "romantic": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Отправляюсь в поход или путешествие",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    }
                ]
            }
        }

class TestTemplate(BaseModel):
    """Шаблон теста"""
    id: str = Field(..., description="Уникальный ID шаблона")
    name: str = Field(..., description="Название теста")
    description: str = Field(..., description="Описание теста")
    version: str = Field(default="1.0.0")
    
    # Конфигурация теста
    question_count: int = Field(default=10, ge=1, le=50)
    time_limit_minutes: int = Field(default=30, ge=5, le=180)
    pass_threshold: float = Field(default=60.0, ge=0, le=100)
    
    # Вопросы
    question_pool: List[str] = Field(
        default_factory=list,
        description="ID вопросов, из которых будет формироваться тест"
    )
    
    # Настройки выборки
    sampling_strategy: str = Field(
        default="random",
        description="Стратегия выборки вопросов: random, balanced, adaptive"
    )
    
    # Интерпретации результатов
    personality_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Описания типов личности"
    )
    
    recommendations: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Рекомендации по типам личности"
    )
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "personality_test_v1",
                "name": "Тест на определение типа личности",
                "description": "Определите ваш тип личности для лучшего подбора партнера",
                "question_count": 10,
                "time_limit_minutes": 30,
                "question_pool": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11", "q12", "q13", "q14", "q15"]
            }
        }