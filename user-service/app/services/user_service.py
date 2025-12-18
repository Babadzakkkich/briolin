from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, func
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional, List, Tuple

from app.database.models import User
from app.schemas.user import UserUpdate
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.core.logger import logger


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: UUID) -> User:
        """Получение пользователя по ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundException("User not found")
        
        return user
    
    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Получение пользователя по Keycloak ID"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        stmt = select(User).where(User.username == username.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate
    ) -> User:
        """Обновление пользователя в локальной БД"""
        user = await self.get_user_by_id(user_id)
        
        # Сохраняем старые значения для проверки уникальности
        old_email = user.email
        old_username = user.username
        
        # Проверяем уникальность email и username среди других пользователей
        update_data = user_data.model_dump(exclude_unset=True)
        
        if 'email' in update_data or 'username' in update_data:
            conditions = []
            if 'email' in update_data and update_data['email'] != old_email:
                conditions.append(User.email == update_data['email'].lower())
            if 'username' in update_data and update_data['username'] != old_username:
                conditions.append(User.username == update_data['username'].lower())
            
            if conditions:
                stmt = select(User).where(or_(*conditions), User.id != user_id)
                result = await self.db.execute(stmt)
                if result.scalar_one_or_none():
                    raise UserAlreadyExistsException("Email or username already taken")
        
        # Применяем обновления к локальному пользователю
        for field, value in update_data.items():
            if field in ['email', 'username']:
                value = value.lower()
            setattr(user, field, value)
        
        try:
            # Обновляем в локальной БД
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Удаление пользователя (soft delete в БД)"""
        user = await self.get_user_by_id(user_id)
        
        try:
            # Soft delete в локальной БД
            user.is_active = False
            await self.db.commit()
            
            logger.info(f"User {user_id} deactivated")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Получение списка пользователей с пагинацией"""
        query = select(User)
        
        # Применяем фильтры
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        
        # Получаем общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Применяем пагинацию
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        # Выполняем запрос
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    async def toggle_user_status(self, user_id: UUID) -> User:
        """Переключение статуса активности пользователя"""
        user = await self.get_user_by_id(user_id)
        
        try:
            # Меняем статус в локальной БД
            new_status = not user.is_active
            user.is_active = new_status
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User {user_id} status changed to {user.is_active}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to toggle user status {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change user status"
            )
    
    async def create_user(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str
    ) -> User:
        """Создание пользователя в локальной БД (для синхронизации)"""
        # Проверка существования пользователя
        stmt = select(User).where(
            (User.email == email) | 
            (User.username == username) | 
            (User.keycloak_id == keycloak_id)
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException("User already exists")
        
        # Создание пользователя
        new_user = User(
            keycloak_id=keycloak_id,
            email=email.lower(),
            username=username.lower(),
            first_name=first_name,
            last_name=last_name
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            logger.info(f"User created in user-service: {new_user.id}")
            return new_user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )