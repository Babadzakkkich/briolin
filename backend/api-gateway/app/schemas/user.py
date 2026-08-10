from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, Any, Dict
from shared.schemas.shared import UserRole

class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    keycloak_id: str
    username: str
    email: EmailStr
    is_active: bool
    roles: List[UserRole]
    created_at: datetime

class UserList(BaseModel):
    users: List[UserPublic]
    total: int
    page: int
    size: int

class UserRolesUpdate(BaseModel):
    roles: List[UserRole]

class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    keycloak_id: str
    username: str
    email: str
    roles: List[UserRole]
    is_active: bool
    is_test_passed: bool
    created_at: datetime

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
    user: Optional[Dict[str, Any]] = None
    profile: Optional[Dict[str, Any]] = None