from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TargetedSearchLockInfo(BaseModel):
    """Информация о блокировке таргетированных рекомендаций"""
    is_locked: bool = Field(..., description="Заблокирован ли пользователь")
    profiles_viewed: int = Field(..., description="Просмотрено профилей в текущем периоде")
    daily_limit: int = Field(..., description="Дневной лимит просмотров")
    locked_until: Optional[datetime] = Field(None, description="Время разблокировки")
    time_until_unlock: Optional[int] = Field(None, description="Секунд до разблокировки")