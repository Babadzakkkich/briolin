from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, JSON, Boolean, Column, BigInteger, Index, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class SearchSession(Base):
    """
    Сессии поиска пользователей
    Сохраняет историю поисковых запросов и их результаты
    """
    __tablename__ = "search_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    keycloak_id: Mapped[str] = mapped_column(String, nullable=False, index=True)  # Добавлено для связи
    search_type: Mapped[str] = mapped_column(String(50), nullable=False, default='classic')
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    results: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)  # ID профилей
    viewed_profiles: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    current_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_results: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )