from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from shared.schemas.shared import Gender


class BasicProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gender: Gender
    date_of_birth: date
    city: str = Field(..., min_length=1, max_length=200)


class BasicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    keycloak_id: str
    first_name: str
    last_name: str
    gender: Gender
    date_of_birth: date
    city: str
    online: bool
    avatar_url: Optional[str] = None  # Добавляем
    thumbnail_url: Optional[str] = None  # Добавляем
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]


class BasicProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    city: Optional[str] = Field(None, min_length=1, max_length=200)


class DetailedProfileCreate(BaseModel):
    about_me: str = Field(..., min_length=10, max_length=2000)
    education: str = Field(..., min_length=1, max_length=500)
    hobbies: str = Field(..., min_length=1, max_length=1000)
    partner_preferences: str = Field(..., min_length=10, max_length=2000)


class DetailedProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    about_me: str
    education: str
    hobbies: str
    partner_preferences: str


class DetailedProfileUpdate(BaseModel):
    about_me: Optional[str] = Field(None, min_length=10, max_length=2000)
    education: Optional[str] = Field(None, min_length=1, max_length=500)
    hobbies: Optional[str] = Field(None, min_length=1, max_length=1000)
    partner_preferences: Optional[str] = Field(None, min_length=10, max_length=2000)


class FullProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    basic: BasicProfileResponse
    detailed: Optional[DetailedProfileResponse] = None


class FullProfileCreate(BaseModel):
    basic: BasicProfileCreate
    detailed: DetailedProfileCreate


class FullProfileUpdate(BaseModel):
    basic: Optional[BasicProfileUpdate] = None
    detailed: Optional[DetailedProfileUpdate] = None


class ProfileListResponse(BaseModel):
    profiles: list[BasicProfileResponse]
    total: int
    page: int
    size: int


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