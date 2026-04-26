import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
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
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # embedding vector for semantic search (dimension 384)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384), nullable=True)
    
    sentiment_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(3), nullable=True)
    
    detailed_profile: Mapped["DetailedProfile"] = relationship(
        "DetailedProfile",
        back_populates="basic_profile",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    questions: Mapped[Optional["ProfileQuestions"]] = relationship(
        "ProfileQuestions",
        back_populates="basic_profile",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DetailedProfile(Base):
    __tablename__ = "detailed_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    basic_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("basic_profiles.id", ondelete="CASCADE"), unique=True)
    
    about_me: Mapped[str] = mapped_column(Text, nullable=False)
    education: Mapped[str] = mapped_column(String, nullable=False)
    hobbies: Mapped[str] = mapped_column(Text, nullable=False)
    partner_preferences: Mapped[str] = mapped_column(Text, nullable=False)
    
    # NEW: Red flags - список вещей, которые пользователь НЕ приемлет
    red_flags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(200)), nullable=True)
    
    basic_profile: Mapped["BasicProfile"] = relationship(
        "BasicProfile",
        back_populates="detailed_profile"
    )
    
class ProfileQuestions(Base):
    """Вопросы пользователя для предварительного знакомства"""
    __tablename__ = "profile_questions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    basic_profile_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("basic_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )
    question_1: Mapped[str] = mapped_column(String(500), nullable=False)
    question_2: Mapped[str] = mapped_column(String(500), nullable=False)
    question_3: Mapped[str] = mapped_column(String(500), nullable=False)
    question_4: Mapped[str] = mapped_column(String(500), nullable=False)
    question_5: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    basic_profile: Mapped["BasicProfile"] = relationship(
        "BasicProfile", 
        back_populates="questions"
    )