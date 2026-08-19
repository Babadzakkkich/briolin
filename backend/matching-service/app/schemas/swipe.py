from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class LikeRequest(BaseModel):
    """Запрос на лайк"""
    target_user_id: str = Field(..., description='Keycloak ID пользователя, к которому относится действие')


class DislikeRequest(BaseModel):
    """Запрос на дизлайк"""
    target_user_id: str = Field(..., description='Keycloak ID пользователя, к которому относится действие')


class SwipeResponse(BaseModel):
    """Схема ответа на лайк или дизлайк с информацией о возможном совпадении."""
    match: bool = Field(..., description='Признак возникновения взаимного совпадения пользователей')
    match_id: Optional[int] = Field(None, description='Уникальный идентификатор совпадения пользователей')
    chat_id: Optional[UUID] = Field(None, description='Идентификатор чата, созданного при взаимном совпадении')


class SwipeStatusResponse(BaseModel):
    """Схема текущего статуса реакции пользователя на другой профиль."""
    swiped: bool = Field(..., description='Признак наличия ранее выполненного свайпа для пользователя')
    type: Optional[str] = Field(None, description='Тип ранее выполненного свайпа')  # 'like' or 'dislike'