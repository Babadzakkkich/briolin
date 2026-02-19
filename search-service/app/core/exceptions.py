class SearchServiceException(Exception):
    """Базовый класс для ошибок search-service"""
    def __init__(self, message: str = "Search service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SearchSessionNotFoundException(SearchServiceException):
    """Исключение при ненайденной сессии поиска"""
    def __init__(self, message: str = "Search session not found"):
        super().__init__(message=message, status_code=404)


class DatabaseException(SearchServiceException):
    """Исключение при ошибках базы данных"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)


class InvalidSearchParametersException(SearchServiceException):
    """Исключение при неверных параметрах поиска"""
    def __init__(self, message: str = "Invalid search parameters"):
        super().__init__(message=message, status_code=400)


class SearchLockedException(SearchServiceException):
    """Исключение при блокировке поиска"""
    def __init__(self, message: str = "Search is locked", unlock_time=None, time_until_unlock=None, profiles_viewed=0):
        self.unlock_time = unlock_time
        self.time_until_unlock = time_until_unlock
        self.profiles_viewed = profiles_viewed
        super().__init__(message=message, status_code=429)  # 429 Too Many Requests