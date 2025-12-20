class UserServiceException(Exception):
    """Базовый класс для ошибок user-service"""
    def __init__(self, message: str = "User service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class KeycloakConnectionError(UserServiceException):
    """Ошибка связи с Keycloak"""
    def __init__(self, message: str = "Keycloak connection error"):
        super().__init__(message=message, status_code=503)

class UserAlreadyExistsException(UserServiceException):
    def __init__(self, message: str = "User already exists"):
        super().__init__(message=message, status_code=409)

class UserNotFoundException(UserServiceException):
    def __init__(self, message: str = "User not found"):
        super().__init__(message=message, status_code=404)

class ValidationException(UserServiceException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)

class DatabaseException(UserServiceException):
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)

class PermissionDeniedException(UserServiceException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)

class InternalAuthException(UserServiceException):
    def __init__(self, message: str = "Internal authentication failed"):
        super().__init__(message=message, status_code=401)