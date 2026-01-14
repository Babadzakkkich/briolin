import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PSYCHOLOGIST = "psychologist"
    USER = "user"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"