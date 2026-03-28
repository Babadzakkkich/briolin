from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Any, Dict, Optional, List

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int

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

class AsyncOperationResponse(BaseModel):
    status: str = Field(..., description="Статус операции (accepted)")
    message: str = Field(..., description="Сообщение о статусе")
    saga_id: str = Field(..., description="ID саги для отслеживания")
    check_status_url: str = Field(..., description="URL для проверки статуса")

class SagaStepInfo(BaseModel):
    name: str
    status: str
    attempts: int
    error: Optional[str] = None
    created_at: Optional[datetime] = None

class SagaStatusResponse(BaseModel):
    saga_id: str
    name: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    steps: List[SagaStepInfo] = []
    step_results: Optional[Dict[str, Any]] = None
    profile: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None