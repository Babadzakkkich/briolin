from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Boolean, Integer, String, DateTime, JSON, BigInteger, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func


class Base(DeclarativeBase):
    pass


class SearchSession(Base):
    """
    Сессии поиска пользователей
    Сохраняет историю поисковых запросов и их результаты
    """
    __tablename__ = "search_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True,)
    search_type: Mapped[str] = mapped_column(String(50), nullable=False, default='classic',)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False,)
    result_profile_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(255)), nullable=True)
    viewed_profile_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(255)), nullable=True)
    total_results: Mapped[int] = mapped_column(Integer, nullable=False, default=0,)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(),nullable=False,)
    updated_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False,)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,default=lambda: datetime.utcnow() + timedelta(days=30))
    
    @property
    def remaining_profile_ids(self) -> List[int]:
        """Возвращает ID еще не просмотренных профилей"""
        if not self.result_profile_ids:
            return []
        if not self.viewed_profile_ids:
            return self.result_profile_ids
        return [pid for pid in self.result_profile_ids if pid not in self.viewed_profile_ids]
    
    @property
    def viewed_count(self) -> int:
        """Количество просмотренных профилей"""
        return len(self.viewed_profile_ids) if self.viewed_profile_ids else 0
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истекла ли сессия"""
        return datetime.utcnow() > self.expires_at

class SearchLock(Base):
    __tablename__ = "search_locks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keycloak_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    profiles_viewed: Mapped[int] = mapped_column(Integer, default=0)
    lock_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())