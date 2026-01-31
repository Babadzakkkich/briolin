from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

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
    pass

class TestStartResponse(BaseModel):
    session_id: str
    test_name: str
    description: str
    time_limit_minutes: int
    questions: List[Dict[str, Any]]
    started_at: datetime
    expires_at: datetime

class AnswerSubmitRequest(BaseModel):
    answer: Union[str, int, bool, Dict[str, Any]] = Field(...)

class AnswerSubmitResponse(BaseModel):
    session_id: str
    question_id: str
    answer_saved: bool
    total_answered: int
    total_questions: int

class TestCompleteRequest(BaseModel):
    pass

class TestResultsData(BaseModel):
    total_score: float
    max_possible_score: float
    percentage: float
    passed: bool

class TestCompleteResponse(BaseModel):
    session_id: str
    status: TestStatus
    completed_at: datetime
    time_spent_minutes: Optional[float]
    results: TestResultsData
    summary: Dict[str, Any]

class TestResultsResponse(BaseModel):
    session_id: str
    status: TestStatus
    completed_at: datetime
    results: TestResultsData

class TestHistoryItem(BaseModel):
    session_id: str
    test_name: str
    completed_at: datetime
    total_score: float
    percentage: float
    passed: bool

class TestHistoryResponse(BaseModel):
    history: List[TestHistoryItem]
    total: int
    skip: int
    limit: int

class UserTestStatistics(BaseModel):
    total_tests_taken: int
    total_tests_completed: int
    average_score: float
    last_test_date: Optional[datetime]

class AdminQuestionResponse(BaseModel):
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
    explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    detail: str