class ProfileServiceException(Exception):
    """Базовый класс для ошибок profile-service"""
    def __init__(self, message: str = "Profile service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ProfileNotFoundException(ProfileServiceException):
    def __init__(self, message: str = "Profile not found"):
        super().__init__(message=message, status_code=404)

class ProfileAlreadyExistsException(ProfileServiceException):
    def __init__(self, message: str = "Profile already exists"):
        super().__init__(message=message, status_code=409)

class KeycloakConnectionError(ProfileServiceException):
    def __init__(self, message: str = "Keycloak connection error"):
        super().__init__(message=message, status_code=503)

class ValidationException(ProfileServiceException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)

class DatabaseException(ProfileServiceException):
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)

class PermissionDeniedException(ProfileServiceException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)

class InternalAuthException(ProfileServiceException):
    def __init__(self, message: str = "Internal authentication failed"):
        super().__init__(message=message, status_code=401)