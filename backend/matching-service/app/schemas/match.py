from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PartnerInfo(BaseModel):
    """Схема краткой информации о пользователе-партнёре в совпадении."""
    keycloak_id: str = Field(..., description='Keycloak ID пользователя-партнёра')
    display_name: str = Field(..., description='Отображаемое имя пользователя')
    avatar_url: Optional[str] = Field(None, description='URL изображения аватара')


class MatchResponse(BaseModel):
    """Схема ответа с информацией о сформированном совпадении пользователей."""
    match_id: int = Field(..., description='Уникальный идентификатор совпадения пользователей')
    partner: PartnerInfo = Field(..., description='Информация о пользователе, с которым возникло совпадение')
    matched_at: datetime = Field(..., description='Дата и время возникновения совпадения')