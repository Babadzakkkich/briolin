from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from shared.schemas.shared import Gender
from .questions import ProfileQuestionsResponse


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
    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
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
    red_flags: Optional[List[str]] = Field(
        None, 
        max_length=20,
        description="Список вещей, которые пользователь НЕ приемлет в партнёре"
    )


class DetailedProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    about_me: str
    education: str
    hobbies: str
    partner_preferences: str
    red_flags: Optional[List[str]] = None


class DetailedProfileUpdate(BaseModel):
    about_me: Optional[str] = Field(None, min_length=10, max_length=2000)
    education: Optional[str] = Field(None, min_length=1, max_length=500)
    hobbies: Optional[str] = Field(None, min_length=1, max_length=1000)
    partner_preferences: Optional[str] = Field(None, min_length=10, max_length=2000)
    red_flags: Optional[List[str]] = Field(None, max_length=20)


class FullProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    basic: BasicProfileResponse
    detailed: Optional[DetailedProfileResponse] = None
    questions: Optional[ProfileQuestionsResponse] = None


class FullProfileCreate(BaseModel):
    basic: BasicProfileCreate
    detailed: DetailedProfileCreate


class FullProfileUpdate(BaseModel):
    basic: Optional[BasicProfileUpdate] = None
    detailed: Optional[DetailedProfileUpdate] = None