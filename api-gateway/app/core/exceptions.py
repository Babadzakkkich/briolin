class GatewayException(Exception):
    """Базовый класс для ошибок Gateway"""
    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)

class ServiceUnavailableException(GatewayException):
    """Сервис недоступен"""
    def __init__(self, service_name: str):
        super().__init__(
            detail=f"Service {service_name} is unavailable",
            status_code=503
        )

class AuthenticationException(GatewayException):
    """Ошибка аутентификации"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=401)

class AuthorizationException(GatewayException):
    """Ошибка авторизации"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(detail=detail, status_code=403)