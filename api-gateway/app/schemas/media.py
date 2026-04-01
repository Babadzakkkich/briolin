from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class AvatarUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    avatar_id: str
    url: str
    thumbnail_url: str
    width: int
    height: int
    file_size: int


class AvatarDeleteResponse(BaseModel):
    deleted: bool
    avatar_id: str


class ErrorResponse(BaseModel):
    detail: str