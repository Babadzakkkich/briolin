class SagaException(Exception):
    """Базовое исключение для SAGA"""
    def __init__(self, message: str = "SAGA error"):
        self.message = message
        super().__init__(self.message)

class SagaStepFailedException(SagaException):
    """Исключение при неудачном выполнении шага SAGA"""
    def __init__(self, message: str = "SAGA step failed"):
        super().__init__(message=message)

class SagaCompensationException(SagaException):
    """Исключение при неудачной компенсации"""
    def __init__(self, message: str = "SAGA compensation failed"):
        super().__init__(message=message)

class SagaTimeoutException(SagaException):
    """Исключение при таймауте SAGA"""
    def __init__(self, message: str = "SAGA timed out"):
        super().__init__(message=message)