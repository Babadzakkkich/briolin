import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from shared.schemas.shared import UserRole

class Base(DeclarativeBase):
    pass

class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="role_assignments")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role', name='uq_user_role'),
    )

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    role_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    
    @property
    def roles(self) -> List[UserRole]:
        return [assignment.role for assignment in self.role_assignments]