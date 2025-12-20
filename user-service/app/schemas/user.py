from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
import enum
from shared.schemas.shared import UserRole

class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
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
    id: int
    keycloak_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime