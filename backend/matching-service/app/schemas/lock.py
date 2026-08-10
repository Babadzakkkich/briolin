from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TargetedSearchLockInfo(BaseModel):
    """Информация о блокировке таргетированных рекомендаций (эмбеддинги)"""
    is_locked: bool = Field(..., description='Признак блокировки таргетированного поиска')
    profiles_viewed: int = Field(..., description='Количество просмотренных профилей')
    daily_limit: int = Field(..., description='Суточный лимит операций')
    locked_until: Optional[datetime] = Field(None, description='Дата и время окончания блокировки')
    time_until_unlock: Optional[int] = Field(None, description='Количество секунд до снятия блокировки')


class LikeUsageInfo(BaseModel):
    """Информация об использовании лайков"""
    likes_used_today: int = Field(..., description='Количество лайков, использованных за текущие сутки')
    daily_like_limit: int = Field(..., description='Суточный лимит лайков')
    likes_remaining: int = Field(..., description='Количество лайков, оставшихся до суточного лимита')