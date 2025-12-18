class UserException(Exception):
    """Базовый класс для ошибок пользователей"""
    pass

class UserAlreadyExistsException(UserException):
    """Пользователь с таким email или username уже существует"""
    def __init__(self, message: str = "User already exists"):
        self.message = message
        super().__init__(self.message)

class UserNotFoundException(UserException):
    """Пользователь не найден"""
    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)