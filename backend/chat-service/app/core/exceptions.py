class ChatServiceException(Exception):
    """Базовый класс для ошибок chat-service"""
    def __init__(self, message: str = "Chat service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class WebSocketException(ChatServiceException):
    """Ошибка WebSocket соединения"""
    def __init__(self, message: str = "WebSocket error"):
        super().__init__(message=message, status_code=400)

class RateLimitException(ChatServiceException):
    """Превышен лимит запросов"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)

class ChatNotFoundException(ChatServiceException):
    """Чат не найден"""
    def __init__(self, message: str = "Chat not found"):
        super().__init__(message=message, status_code=404)

class MessageNotFoundException(ChatServiceException):
    """Сообщение не найдено"""
    def __init__(self, message: str = "Message not found"):
        super().__init__(message=message, status_code=404)

class PermissionDeniedException(ChatServiceException):
    """Доступ запрещен"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)

class DatabaseException(ChatServiceException):
    """Ошибка базы данных"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)

class ValidationException(ChatServiceException):
    """Ошибка валидации"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)