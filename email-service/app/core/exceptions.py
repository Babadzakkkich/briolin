class EmailException(Exception):
    """Базовый класс для ошибок email-сервиса"""
    def __init__(self, message: str = "Email error", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SmtpConnectionError(EmailException):
    """Ошибка подключения к SMTP"""
    def __init__(self, message: str = "SMTP connection error"):
        super().__init__(message=message, status_code=503)


class TemplateNotFoundError(EmailException):
    """Шаблон не найден"""
    def __init__(self, message: str = "Email template not found"):
        super().__init__(message=message, status_code=404)


class InvalidEmailError(EmailException):
    """Неверный email адрес"""
    def __init__(self, message: str = "Invalid email address"):
        super().__init__(message=message, status_code=400)


class SendEmailError(EmailException):
    """Ошибка отправки email"""
    def __init__(self, message: str = "Failed to send email"):
        super().__init__(message=message, status_code=500)