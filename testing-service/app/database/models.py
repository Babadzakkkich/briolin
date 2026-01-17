import enum
from datetime import datetime, timedelta
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum  # ДОБАВЛЕНО
import uuid

class Base(DeclarativeBase):
    pass

class PersonalityType(str, enum.Enum):
    ROMANTIC = "romantic"
    ADVENTURER = "adventurer"
    INTELLECTUAL = "intellectual"
    CAREGIVER = "caregiver"
    LEADER = "leader"
    FREE_SPIRIT = "free_spirit"

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
    status: Mapped[TestStatus] = mapped_column(SQLEnum(TestStatus), default=TestStatus.CREATED)  # ИСПРАВЛЕНО
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

class TestResult(Base):
    __tablename__ = "test_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_sessions.id", ondelete="CASCADE"))
    keycloak_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    # Результаты по типам личности
    romantic_score: Mapped[float] = mapped_column(Float, default=0.0)
    adventurer_score: Mapped[float] = mapped_column(Float, default=0.0)
    intellectual_score: Mapped[float] = mapped_column(Float, default=0.0)
    caregiver_score: Mapped[float] = mapped_column(Float, default=0.0)
    leader_score: Mapped[float] = mapped_column(Float, default=0.0)
    free_spirit_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # ИСПРАВЛЕНО: Используем SQLEnum для правильного хранения и загрузки Enum значений
    primary_personality: Mapped[PersonalityType] = mapped_column(SQLEnum(PersonalityType), nullable=True)
    secondary_personality: Mapped[PersonalityType] = mapped_column(SQLEnum(PersonalityType), nullable=True)
    
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    max_possible_score: Mapped[float] = mapped_column(Float, default=100.0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    interpretation: Mapped[str] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    session: Mapped["TestSession"] = relationship(back_populates="result")
    
    @property
    def personality_scores(self) -> dict:
        """Возвращает все баллы по типам личности в виде словаря"""
        return {
            "romantic": self.romantic_score,
            "adventurer": self.adventurer_score,
            "intellectual": self.intellectual_score,
            "caregiver": self.caregiver_score,
            "leader": self.leader_score,
            "free_spirit": self.free_spirit_score,
        }

class UserTestStatistics(Base):
    __tablename__ = "user_test_statistics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    total_tests_taken: Mapped[int] = mapped_column(Integer, default=0)
    total_tests_completed: Mapped[int] = mapped_column(Integer, default=0)
    average_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Распределение по типам личности
    primary_romantic_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_adventurer_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_intellectual_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_caregiver_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_leader_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_free_spirit_count: Mapped[int] = mapped_column(Integer, default=0)
    
    last_test_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_primary_personality_distribution(self) -> dict:
        """Возвращает распределение основных типов личности"""
        return {
            PersonalityType.ROMANTIC: self.primary_romantic_count,
            PersonalityType.ADVENTURER: self.primary_adventurer_count,
            PersonalityType.INTELLECTUAL: self.primary_intellectual_count,
            PersonalityType.CAREGIVER: self.primary_caregiver_count,
            PersonalityType.LEADER: self.primary_leader_count,
            PersonalityType.FREE_SPIRIT: self.primary_free_spirit_count,
        }