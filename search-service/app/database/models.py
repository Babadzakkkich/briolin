from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, JSON, Boolean, Column, Date, BigInteger, Index, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from shared.schemas.shared import Gender


class Base(DeclarativeBase):
    pass


class BasicProfile(Base):
    __tablename__ = "basic_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[Gender] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    detailed_profile: Mapped["DetailedProfile"] = relationship(
        "DetailedProfile",
        back_populates="basic_profile",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DetailedProfile(Base):
    __tablename__ = "detailed_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    basic_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("basic_profiles.id", ondelete="CASCADE"),
                                                  unique=True)

    about_me: Mapped[str] = mapped_column(Text, nullable=False)
    education: Mapped[str] = mapped_column(String, nullable=False)
    hobbies: Mapped[str] = mapped_column(Text, nullable=False)
    partner_preferences: Mapped[str] = mapped_column(Text, nullable=False)

    basic_profile: Mapped["BasicProfile"] = relationship(
        "BasicProfile",
        back_populates="detailed_profile"
    )

class SearchSession(Base):
    """
    Сессии поиска пользователей
    Сохраняет историю поисковых запросов и их результаты
    """
    __tablename__ = "search_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    search_type: Mapped[str] = mapped_column(String(50), nullable=False, default='classic')
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    results: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
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

    # Композитные индексы
    __table_args__ = (
        Index('ix_search_sessions_user_created', 'user_id', 'created_at'),
        Index('ix_search_sessions_user_type', 'user_id', 'search_type'),
        Index('ix_search_sessions_created_at', 'created_at'),
    )