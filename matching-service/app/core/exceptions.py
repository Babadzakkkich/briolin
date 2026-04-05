class MatchingServiceException(Exception):
    """Base exception for matching service"""
    def __init__(self, message: str = "Matching service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SwipeLimitExceededException(MatchingServiceException):
    def __init__(self, message: str = "Daily swipe limit exceeded"):
        super().__init__(message=message, status_code=429)


class UserNotFoundException(MatchingServiceException):
    def __init__(self, message: str = "User not found"):
        super().__init__(message=message, status_code=404)


class AlreadySwipedException(MatchingServiceException):
    def __init__(self, message: str = "Already swiped on this user"):
        super().__init__(message=message, status_code=409)


class ProfileServiceException(MatchingServiceException):
    def __init__(self, message: str = "Profile service error"):
        super().__init__(message=message, status_code=503)


class SearchServiceException(MatchingServiceException):
    def __init__(self, message: str = "Search service error"):
        super().__init__(message=message, status_code=503)


class DatabaseException(MatchingServiceException):
    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)