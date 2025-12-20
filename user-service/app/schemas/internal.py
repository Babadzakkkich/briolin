from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime
from shared.schemas.shared import UserRole

class UserProfileCreate(BaseModel):
    keycloak_id: str
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole

class UserProfileResponse(BaseModel):
    keycloak_id: str
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime