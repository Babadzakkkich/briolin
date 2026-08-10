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
    """Схема запроса на запуск нового тестирования пользователя."""
    pass


class TestStartResponse(BaseModel):
    """Схема ответа с данными запущенной тестовой сессии и набором вопросов."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    test_name: str = Field(..., description='Название теста')
    description: str = Field(..., description='Описание запущенного теста')
    time_limit_minutes: int = Field(..., description='Лимит времени на прохождение теста в минутах')
    questions: List[Dict[str, Any]] = Field(..., description='Список вопросов')
    started_at: datetime = Field(..., description='Дата и время начала тестирования')
    expires_at: datetime = Field(..., description='Дата и время истечения срока действия')
    time_left_seconds: int = Field(..., description='Оставшееся время прохождения теста в секундах')  # Добавлено


class AnswerSubmitRequest(BaseModel):
    """Схема запроса на сохранение ответа пользователя на вопрос теста."""
    answer: Union[str, int, bool, Dict[str, Any]] = Field(..., description='Ответ пользователя на вопрос теста')


class AnswerSubmitResponse(BaseModel):
    """Схема ответа с результатом сохранения ответа на вопрос теста."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    question_id: str = Field(..., description='Уникальный идентификатор вопроса')
    answer_saved: bool = Field(..., description='Признак успешного сохранения ответа')
    total_answered: int = Field(..., description='Количество сохранённых ответов пользователя')
    total_questions: int = Field(..., description='Общее количество вопросов')


class TestCompleteRequest(BaseModel):
    """Схема запроса на досрочное или штатное завершение текущего теста."""
    pass


class TestResultsData(BaseModel):
    """Схема итоговых показателей и результата прохождения теста."""
    total_score: float = Field(..., description='Количество баллов, набранных за тест')
    max_possible_score: float = Field(..., description='Максимально возможное количество баллов за тест')
    percentage: float = Field(..., description='Результат теста в процентах')
    passed: bool = Field(..., description='Признак успешного прохождения теста')


class TestCompleteResponse(BaseModel):
    """Схема ответа с итогами завершённой тестовой сессии."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    status: TestStatus = Field(..., description='Статус завершённой тестовой сессии')
    completed_at: datetime = Field(..., description='Дата и время завершения операции')
    time_spent_minutes: Optional[float] = Field(..., description='Фактическое время прохождения теста в минутах')
    results: TestResultsData = Field(..., description='Результаты прохождения теста')
    summary: Dict[str, Any] = Field(..., description='Сводная информация по результатам теста')


class TestResultsResponse(BaseModel):
    """Схема ответа с сохранёнными результатами конкретной тестовой сессии."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    status: TestStatus = Field(..., description='Статус тестовой сессии')
    completed_at: datetime = Field(..., description='Дата и время завершения операции')
    results: TestResultsData = Field(..., description='Результаты прохождения теста')


class TestHistoryItem(BaseModel):
    """Схема краткой информации об одном завершённом тестировании пользователя."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    test_name: str = Field(..., description='Название теста')
    completed_at: datetime = Field(..., description='Дата и время завершения операции')
    total_score: float = Field(..., description='Количество баллов, набранных за тест')
    percentage: float = Field(..., description='Результат теста в процентах')
    passed: bool = Field(..., description='Признак успешного прохождения теста')


class TestHistoryResponse(BaseModel):
    """Схема ответа с историей прохождения тестов и параметрами пагинации."""
    history: List[TestHistoryItem] = Field(..., description='Список записей истории прохождения тестов')
    total: int = Field(..., description='Общее количество элементов')
    skip: int = Field(..., description='Количество элементов, пропускаемых перед выдачей результата')
    limit: int = Field(..., description='Максимальное количество элементов в результате')


class UserTestStatistics(BaseModel):
    """Схема агрегированной статистики прохождения тестов пользователем."""
    total_tests_taken: int = Field(..., description='Общее количество начатых тестов')
    total_tests_completed: int = Field(..., description='Количество завершённых тестов')
    average_score: float = Field(..., description='Средний результат пользователя по завершённым тестам')
    last_test_date: Optional[datetime] = Field(..., description='Дата и время последнего пройденного теста')


class AdminQuestionResponse(BaseModel):
    """Схема полной информации о тестовом вопросе для административных операций."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description='Уникальный идентификатор вопроса')
    text: str = Field(..., description='Текст вопроса')
    question_type: QuestionType = Field(..., description='Тип вопроса')
    difficulty: str = Field(..., description='Уровень сложности вопроса')
    category: str = Field(..., description='Категория вопроса')
    tags: List[str] = Field(..., description='Список тегов вопроса')
    options: List[Dict[str, Any]] = Field(..., description='Доступные варианты ответа на вопрос')
    min_value: Optional[int] = Field(None, description='Минимально допустимое значение ответа')
    max_value: Optional[int] = Field(None, description='Максимально допустимое значение ответа')
    labels: Optional[Dict[int, str]] = Field(None, description='Подписи значений или вариантов ответа')
    explanation: Optional[str] = Field(None, description='Пояснение к вопросу или правильному ответу')
    created_at: datetime = Field(..., description='Дата и время создания записи')
    updated_at: datetime = Field(..., description='Дата и время последнего обновления записи')


class ErrorResponse(BaseModel):
    """Схема стандартного ответа API с описанием ошибки."""
    detail: Union[str, Dict[str, Any]] = Field(..., description='Подробное описание ошибки')


class CurrentTestQuestion(BaseModel):
    """Вопрос в текущем тесте"""
    id: str = Field(..., description='Уникальный идентификатор вопроса')
    text: str = Field(..., description='Текст вопроса')
    question_type: QuestionType = Field(..., description='Тип вопроса')
    difficulty: str = Field(..., description='Уровень сложности вопроса')
    category: str = Field(..., description='Категория вопроса')
    tags: List[str] = Field(..., description='Список тегов вопроса')
    options: List[Dict[str, Any]] = Field(..., description='Доступные варианты ответа на вопрос')
    min_value: Optional[int] = Field(None, description='Минимально допустимое значение ответа')
    max_value: Optional[int] = Field(None, description='Максимально допустимое значение ответа')
    labels: Optional[Dict[int, str]] = Field(None, description='Подписи значений или вариантов ответа')
    answered: bool = Field(False, description='Признак наличия сохранённого ответа на вопрос')
    saved_answer: Optional[Any] = Field(None, description='Сохранённый ответ пользователя на вопрос')

class CurrentTestResponse(BaseModel):
    """Схема ответа с полной информацией о текущем активном тесте пользователя."""
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    test_name: str = Field(..., description='Название теста')
    description: str = Field(..., description='Описание текущего теста')
    status: str = Field(..., description='Текущий статус тестовой сессии')
    started_at: datetime = Field(..., description='Дата и время начала тестирования')
    expires_at: datetime = Field(..., description='Дата и время истечения срока действия')
    time_left_seconds: int = Field(..., description='Оставшееся время прохождения теста в секундах')
    time_limit_minutes: int = Field(..., description='Лимит времени на прохождение теста в минутах')
    total_questions: int = Field(..., description='Общее количество вопросов')
    answered_questions: int = Field(..., description='Количество вопросов, на которые пользователь уже ответил')
    questions: List[CurrentTestQuestion] = Field(..., description='Список вопросов')


class ActiveTestErrorResponse(BaseModel):
    """Схема ошибки, возникающей при наличии уже активной тестовой сессии."""
    detail: str = Field(..., description='Подробное описание ошибки')
    session_id: str = Field(..., description='Уникальный идентификатор сессии тестирования')
    action: str = Field(..., description='Название выполняемого действия')