from pydantic import BaseModel, EmailStr, Field


class VerifyCodeRequest(BaseModel):
    """Схема запроса на подтверждение операции с помощью проверочного кода."""
    code: str = Field(..., description='Код подтверждения')

class PasswordResetRequest(BaseModel):
    """Схема запроса на начало процедуры восстановления пароля пользователя."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')


class PasswordResetConfirmRequest(BaseModel):
    """Схема запроса на подтверждение восстановления и установку нового пароля."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    code: str = Field(..., description='Код подтверждения')
    new_password: str = Field(..., min_length=6, description='Новый пароль пользователя')