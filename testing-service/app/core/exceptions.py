class TestingException(Exception):
    """Базовый класс для ошибок тестирования"""
    def __init__(self, message: str = "Testing error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TestNotFoundException(TestingException):
    """Тест не найден"""
    def __init__(self, message: str = "Test not found"):
        super().__init__(message=message, status_code=404)

class QuestionNotFoundException(TestingException):
    """Вопрос не найден"""
    def __init__(self, message: str = "Question not found"):
        super().__init__(message=message, status_code=404)

class TestAlreadyCompletedException(TestingException):
    """Тест уже завершен"""
    def __init__(self, message: str = "Test already completed"):
        super().__init__(message=message, status_code=409)

class DailyLimitExceededException(TestingException):
    """Превышен дневной лимит попыток"""
    def __init__(self, message: str = "Daily attempt limit exceeded"):
        super().__init__(message=message, status_code=429)

class TestTimeLimitExceededException(TestingException):
    """Превышено время на прохождение теста"""
    def __init__(self, message: str = "Test time limit exceeded"):
        super().__init__(message=message, status_code=400)

class InvalidAnswerException(TestingException):
    """Неверный формат ответа"""
    def __init__(self, message: str = "Invalid answer format"):
        super().__init__(message=message, status_code=400)

class DatabaseException(TestingException):
    """Ошибка базы данных"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)

class MongoDBException(TestingException):
    """Ошибка MongoDB"""
    def __init__(self, message: str = "MongoDB error"):
        super().__init__(message=message, status_code=500)

class ActiveTestSessionExistsException(TestingException):
    """Активная сессия теста уже существует"""
    def __init__(self, message: str = "Active test session already exists", session_id: str = None):
        self.session_id = session_id
        super().__init__(message=message, status_code=409)