from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
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
    is_test_passed: bool
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