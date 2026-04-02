# app/database/models.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Avatar(Base):
    __tablename__ = "avatars"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keycloak_id = Column(String(255), nullable=False, index=True)
    
    # Основные метаданные
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    
    # Пути в MinIO
    original_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=False)
    
    # Статусы
    is_current = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)