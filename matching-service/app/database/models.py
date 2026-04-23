from datetime import datetime, date
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, UniqueConstraint, Index, Integer, Date
from sqlalchemy.orm import DeclarativeBase


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


class TargetedSearchLock(Base):
    """Блокировка таргетированных рекомендаций по просмотрам профилей (эмбеддинги)"""
    __tablename__ = "targeted_search_locks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keycloak_id = Column(String(255), unique=True, index=True, nullable=False)
    is_locked = Column(Boolean, default=False)
    locked_until = Column(DateTime, nullable=True)
    profiles_viewed = Column(Integer, default=0)
    period_start = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyLikeUsage(Base):
    """Учёт дневных лайков пользователя"""
    __tablename__ = "daily_like_usage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    keycloak_id = Column(String(255), nullable=False, index=True)
    usage_date = Column(Date, default=datetime.utcnow().date, nullable=False)
    likes_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('keycloak_id', 'usage_date', name='uq_daily_like_usage'),
        Index('idx_daily_like_usage_keycloak_date', 'keycloak_id', 'usage_date'),
    )