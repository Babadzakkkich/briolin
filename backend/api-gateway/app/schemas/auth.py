from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    """Внутренний ответ auth-service. Наружу браузеру токены не отдаём."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


class SessionResponse(BaseModel):
    authenticated: bool
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keycloak_id: str
    email: EmailStr
    is_active: bool
