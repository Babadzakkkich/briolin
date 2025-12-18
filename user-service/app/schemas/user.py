from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)

class UserUpdate(UserBase):
    is_active: Optional[bool] = None

class UserPublic(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    users: List[UserPublic]
    total: int
    page: int
    size: int

class UserInfo(BaseModel):
    id: str
    keycloak_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    is_active: bool