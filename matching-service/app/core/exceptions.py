class MatchingServiceException(Exception):
    """Базовое исключение для matching-service"""
    def __init__(self, message: str = "Matching service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SwipeLimitExceededException(MatchingServiceException):
    def __init__(self, message: str = "Дневной лимит свайпов исчерпан"):
        super().__init__(message=message, status_code=429)


class UserNotFoundException(MatchingServiceException):
    def __init__(self, message: str = "Пользователь не найден"):
        super().__init__(message=message, status_code=404)


class AlreadySwipedException(MatchingServiceException):
    def __init__(self, message: str = "Вы уже совершили свайп на этого пользователя"):
        super().__init__(message=message, status_code=409)


class ProfileServiceException(MatchingServiceException):
    def __init__(self, message: str = "Ошибка profile-service"):
        super().__init__(message=message, status_code=503)


class DatabaseException(MatchingServiceException):
    def __init__(self, message: str = "Ошибка базы данных"):
        super().__init__(message=message, status_code=500)


class TargetedSearchLockedException(MatchingServiceException):
    def __init__(self, message: str, unlock_time=None, time_until_unlock=None, swipes_used=0, daily_limit=0):
        self.unlock_time = unlock_time
        self.time_until_unlock = time_until_unlock
        self.swipes_used = swipes_used
        self.daily_limit = daily_limit
        super().__init__(message=message, status_code=429)