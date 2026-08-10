from pydantic import BaseModel, EmailStr, Field


class VerifyCodeRequest(BaseModel):
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=6)