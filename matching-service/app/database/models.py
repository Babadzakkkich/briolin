from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(DeclarativeBase):
    pass


class Swipe(Base):
    __tablename__ = "swipes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_user_id = Column(String(255), nullable=False, index=True)
    to_user_id = Column(String(255), nullable=False, index=True)
    swipe_type = Column(String(10), nullable=False)  # 'like' or 'dislike'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', name='uq_swipe'),
        Index('idx_swipe_from_to', 'from_user_id', 'to_user_id'),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(String(255), nullable=False, index=True)
    user2_id = Column(String(255), nullable=False, index=True)
    matched_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='uq_match'),
        Index('idx_match_users', 'user1_id', 'user2_id'),
    )