from pydantic import BaseModel, EmailStr


class RequestCodeRequest(BaseModel):
    email: EmailStr


class VerifyConfirmRequest(BaseModel):
    code: str


# ========== ДЛЯ ВОССТАНОВЛЕНИЯ ПАРОЛЯ ==========

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str