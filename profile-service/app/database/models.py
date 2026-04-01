import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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
    
    detailed_profile: Mapped["DetailedProfile"] = relationship(
        "DetailedProfile",
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
    
    basic_profile: Mapped["BasicProfile"] = relationship(
        "BasicProfile",
        back_populates="detailed_profile"
    )