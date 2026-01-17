from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

class PersonalityType(str, Enum):
    ROMANTIC = "romantic"
    ADVENTURER = "adventurer"
    INTELLECTUAL = "intellectual"
    CAREGIVER = "caregiver"
    LEADER = "leader"
    FREE_SPIRIT = "free_spirit"

class TestStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    LIKERT_SCALE = "likert_scale"
    TRUE_FALSE = "true_false"

class TestStartRequest(BaseModel):
    """Запрос на начало теста"""
    pass

class TestStartResponse(BaseModel):
    """Ответ при начале теста"""
    session_id: str
    test_name: str
    description: str
    time_limit_minutes: int
    questions: List[Dict[str, Any]]
    started_at: datetime
    expires_at: datetime

class AnswerSubmitRequest(BaseModel):
    """Запрос на сохранение ответа"""
    answer: Union[str, int, bool, Dict[str, Any]] = Field(..., description="Ответ пользователя")

class AnswerSubmitResponse(BaseModel):
    """Ответ при сохранении ответа"""
    session_id: str
    question_id: str
    answer_saved: bool
    total_answered: int
    total_questions: int

class TestCompleteRequest(BaseModel):
    """Запрос на завершение теста"""
    pass

class TestResultsData(BaseModel):
    """Данные результатов теста"""
    primary_personality: PersonalityType
    secondary_personality: PersonalityType
    personality_scores: Dict[str, float]
    total_score: float
    max_possible_score: float
    percentage: float
    interpretation: str
    recommendations: str

class TestCompleteResponse(BaseModel):
    """Ответ при завершении теста"""
    session_id: str
    status: TestStatus
    completed_at: datetime
    time_spent_minutes: Optional[float]
    results: TestResultsData
    summary: Dict[str, Any]

class TestResultsResponse(BaseModel):
    """Ответ с результатами теста"""
    session_id: str
    status: TestStatus
    completed_at: datetime
    results: TestResultsData

class TestHistoryItem(BaseModel):
    """Элемент истории тестов"""
    session_id: str
    test_name: str
    completed_at: datetime
    primary_personality: PersonalityType
    secondary_personality: PersonalityType
    total_score: float
    percentage: float

class TestHistoryResponse(BaseModel):
    """История тестов пользователя"""
    history: List[TestHistoryItem]
    total: int
    skip: int
    limit: int

class PersonalityDistribution(BaseModel):
    """Распределение типов личности"""
    romantic: int = 0
    adventurer: int = 0
    intellectual: int = 0
    caregiver: int = 0
    leader: int = 0
    free_spirit: int = 0

class UserStatisticsResponse(BaseModel):
    """Статистика пользователя по тестам"""
    total_tests_taken: int
    total_tests_completed: int
    average_score: float
    personality_distribution: PersonalityDistribution
    last_test_date: Optional[datetime]
    updated_at: datetime

class AdminQuestionResponse(BaseModel):
    """Ответ с вопросом (админский, с правильными ответами)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    text: str
    question_type: QuestionType
    difficulty: str
    category: str
    tags: List[str]
    options: List[Dict[str, Any]]
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    labels: Optional[Dict[int, str]] = None
    personality_dimensions: List[str]
    explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    """Ответ при ошибке"""
    detail: str