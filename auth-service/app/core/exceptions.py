class AuthException(Exception):
    """Базовый класс для ошибок аутентификации"""
    def __init__(self, message: str = "Authentication error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserAlreadyExistsException(AuthException):
    """Пользователь с таким email или username уже существует"""
    def __init__(self, message: str = "User already exists"):
        super().__init__(message=message, status_code=409)

class KeycloakConnectionError(AuthException):
    """Ошибка связи с Keycloak"""
    def __init__(self, message: str = "Keycloak connection error"):
        super().__init__(message=message, status_code=503)

class InvalidTokenException(AuthException):
    """Неверный или неактивный токен (access или refresh)"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message, status_code=401)

class InvalidCredentialsException(AuthException):
    """Неверный логин или пароль"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, status_code=401)

class UserNotFoundException(AuthException):
    """Пользователь не найден"""
    def __init__(self, message: str = "User not found"):
        super().__init__(message=message, status_code=404)

class PermissionDeniedException(AuthException):
    """Недостаточно прав"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)

class ValidationException(AuthException):
    """Ошибка валидации данных"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)

class DatabaseException(AuthException):
    """Ошибка базы данных"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)

class SagaCompensationError(AuthException):
    """Ошибка при выполнении компенсирующих действий SAGA"""
    def __init__(self, message: str = "Saga compensation error"):
        super().__init__(message=message, status_code=500)