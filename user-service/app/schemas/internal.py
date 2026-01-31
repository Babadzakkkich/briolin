from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime
from shared.schemas.shared import UserRole

class UserProfileCreate(BaseModel):
    keycloak_id: str
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole

class UserProfileResponse(BaseModel):
    keycloak_id: str
    username: str
    email: EmailStr
    roles: List[UserRole]
    is_active: bool
    is_test_passed: bool
    created_at: datetime