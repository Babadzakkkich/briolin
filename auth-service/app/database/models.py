import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, ForeignKey, Table, Column, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# Определение ролей пользователей
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PSYCHOLOGIST = "psychologist"  # психолог
    USER = "user"  # обычный пользователь

# Таблица для связи пользователей и ролей (как в вашем примере)
class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="role_assignments")
    
    # Уникальное ограничение - один пользователь не может иметь одну роль дважды
    __table_args__ = (
        UniqueConstraint('user_id', 'role', name='uq_user_role'),
    )

class User(Base):
    __tablename__ = "users"
    
    # Используем обычный integer вместо UUID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Связь с ролями через отдельную модель (как в вашем примере)
    role_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    
    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"
    
    # Свойство для удобного доступа к ролям
    @property
    def roles(self) -> List[UserRole]:
        return [assignment.role for assignment in self.role_assignments]