from pydantic import BaseModel, EmailStr


class RequestCodeRequest(BaseModel):
    email: EmailStr


class VerifyConfirmRequest(BaseModel):
    code: str