import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PSYCHOLOGIST = "psychologist"
    USER = "user"