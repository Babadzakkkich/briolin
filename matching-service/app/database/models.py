from datetime import datetime, date
from sqlalchemy import JSON, Column, BigInteger, String, DateTime, Boolean, UniqueConstraint, Index, Integer, Date
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

class LikeWithAnswers(Base):
    """
    Лайк с ответами на вопросы.
    Заменяет обычный Swipe для like, когда у пользователя есть вопросы.
    """
    __tablename__ = "likes_with_answers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_user_id = Column(String(255), nullable=False, index=True)
    to_user_id = Column(String(255), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, matched, declined

    # Ответы на вопросы в JSON
    answers = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', name='uq_like_with_answers'),
        Index('idx_like_answers_from_to', 'from_user_id', 'to_user_id'),
        Index('idx_like_answers_to_status', 'to_user_id', 'status'),
    )


class MatchWithAnswers(Base):
    """
    Матч с сохранением ответов на вопросы.
    Содержит ответы обоих пользователей и вопросы для контекста.
    """
    __tablename__ = "matches_with_answers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(String(255), nullable=False, index=True)
    user2_id = Column(String(255), nullable=False, index=True)

    # Ответы пользователей
    user1_answers = Column(JSON, nullable=True)
    user2_answers = Column(JSON, nullable=True)

    # Вопросы для контекста
    user1_questions = Column(JSON, nullable=True)
    user2_questions = Column(JSON, nullable=True)

    matched_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='uq_match_with_answers'),
        Index('idx_match_answers_users', 'user1_id', 'user2_id'),
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