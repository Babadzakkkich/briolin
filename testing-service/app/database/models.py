import enum
from datetime import datetime, timedelta
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Float, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Base(DeclarativeBase):
    pass

class TestStatus(str, enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class TestSession(Base):
    __tablename__ = "test_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    test_template_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[TestStatus] = mapped_column(String, default=TestStatus.CREATED)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=30)
    questions_order: Mapped[list] = mapped_column(JSON, nullable=False)
    user_answers: Mapped[dict] = mapped_column(JSON, default=dict)
    
    result: Mapped["TestResult"] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
    
    def is_expired(self) -> bool:
        if not self.started_at:
            return False
        expiry_time = self.started_at + timedelta(minutes=self.time_limit_minutes)
        return datetime.utcnow() > expiry_time
    
    def get_time_left_seconds(self) -> int:
        """Возвращает количество оставшихся секунд"""
        if not self.started_at:
            return self.time_limit_minutes * 60
        expiry_time = self.started_at + timedelta(minutes=self.time_limit_minutes)
        time_left = (expiry_time - datetime.utcnow()).total_seconds()
        return max(0, int(time_left))

Index(
    'ix_unique_active_session',
    TestSession.keycloak_id,
    postgresql_where=(TestSession.status == TestStatus.IN_PROGRESS),
    unique=True
)

class TestResult(Base):
    __tablename__ = "test_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_sessions.id", ondelete="CASCADE"))
    keycloak_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    max_possible_score: Mapped[float] = mapped_column(Float, default=100.0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    session: Mapped["TestSession"] = relationship(back_populates="result")