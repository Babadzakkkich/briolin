from pydantic import BaseModel, EmailStr, Field


class RequestCodeRequest(BaseModel):
    """Схема запроса на отправку проверочного кода пользователю."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')


class VerifyConfirmRequest(BaseModel):
    """Схема запроса на подтверждение проверочного кода."""
    code: str = Field(..., description='Код подтверждения')


# ========== ДЛЯ ВОССТАНОВЛЕНИЯ ПАРОЛЯ ==========

class PasswordResetRequest(BaseModel):
    """Схема запроса на начало процедуры восстановления пароля пользователя."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')


class PasswordResetConfirmRequest(BaseModel):
    """Схема запроса на подтверждение восстановления и установку нового пароля."""
    email: EmailStr = Field(..., description='Адрес электронной почты пользователя')
    code: str = Field(..., description='Код подтверждения')
    new_password: str = Field(..., description='Новый пароль пользователя')