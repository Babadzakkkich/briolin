from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import json

SagaBase = declarative_base()

class SagaStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

class SagaOutbox(SagaBase):
    """Outbox таблица для событий саги"""
    __tablename__ = "saga_outbox"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    saga_id = Column(String(36), nullable=False, index=True)
    saga_name = Column(String(100), nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default=SagaStatus.PENDING)
    
    # Данные события
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=False, default={})
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Попытки
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_error = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('ix_saga_outbox_status_created', 'status', 'created_at'),
        Index('ix_saga_outbox_saga_step', 'saga_id', 'step_name', unique=True),
    )

class SagaInstance(SagaBase):
    """Экземпляр саги для отслеживания состояния"""
    __tablename__ = "saga_instances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    saga_id = Column(String(36), unique=True, nullable=False, index=True)
    saga_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default=SagaStatus.PENDING)
    
    # Контекст саги (данные, передаваемые между шагами)
    context = Column(JSON, nullable=False, default={})
    
    # Результаты шагов
    step_results = Column(JSON, nullable=False, default={})
    compensation_results = Column(JSON, nullable=False, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    error = Column(String(500), nullable=True)