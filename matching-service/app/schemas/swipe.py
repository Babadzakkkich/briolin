from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


class SwipeRequest(BaseModel):
    """Запрос на свайп (для обратной совместимости)"""
    target_user_id: str = Field(..., description="Keycloak ID of the target user")
    action: str = Field(..., pattern="^(like|dislike)$", description="like or dislike")


class LikeRequest(BaseModel):
    """Запрос на лайк"""
    target_user_id: str = Field(..., description="Keycloak ID of the target user")


class DislikeRequest(BaseModel):
    """Запрос на дизлайк"""
    target_user_id: str = Field(..., description="Keycloak ID of the target user")


class SwipeResponse(BaseModel):
    match: bool = Field(..., description="Whether a mutual match occurred")
    match_id: Optional[int] = Field(None, description="Match ID if match=true")
    chat_id: Optional[UUID] = Field(None, description="Chat ID if match=true")


class SwipeStatusResponse(BaseModel):
    swiped: bool
    type: Optional[str] = None  # 'like' or 'dislike'