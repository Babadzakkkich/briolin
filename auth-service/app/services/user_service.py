from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func
from typing import Optional, List, Tuple

from app.database.models import User, UserRoleAssignment, UserRole
from app.schemas.user import UserBase, UserRolesUpdate
from app.services.keycloak_client import KeycloakClient
from app.core.exceptions import (
    UserAlreadyExistsException, 
    UserNotFoundException,
    DatabaseException,
    ValidationException,
    KeycloakConnectionError
)
from app.core.logger import logger


class UserService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
    
    async def get_user_by_id(self, user_id: int) -> User:
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
    
    def _update_user_in_keycloak(self, keycloak_id: str, update_data: dict, roles: List[UserRole] = None) -> None:
        """Синхронное обновление пользователя в Keycloak"""
        try:
            # Подготавливаем данные для Keycloak
            kc_data = {}
            
            # Теперь включаем все поля, включая username
            if 'email' in update_data:
                kc_data['email'] = update_data['email']
            if 'username' in update_data:
                kc_data['username'] = update_data['username']
            if 'first_name' in update_data:
                kc_data['firstName'] = update_data['first_name']
            if 'last_name' in update_data:
                kc_data['lastName'] = update_data['last_name']
            
            # Обновляем пользователя в Keycloak с ролями
            self.kc.update_user_in_keycloak(
                keycloak_id=keycloak_id,
                user_data=kc_data if kc_data else None,
                roles=[role.value for role in roles] if roles else None
            )
            
            if kc_data:
                updated_fields = list(kc_data.keys())
                # Маскируем чувствительные данные в логах
                safe_fields = []
                for field in updated_fields:
                    if field == 'username':
                        safe_fields.append(f'username={kc_data[field][:3]}***')
                    else:
                        safe_fields.append(f'{field}=***')
                logger.info(f"User {keycloak_id} updated in Keycloak: {', '.join(safe_fields)}")
            if roles:
                logger.info(f"User {keycloak_id} roles updated in Keycloak: {[role.value for role in roles]}")
                
        except Exception as e:
            logger.error(f"Failed to update user {keycloak_id} in Keycloak: {e}")
            # Пробрасываем исключение, чтобы вызывающий код мог откатить изменения
            raise KeycloakConnectionError(f"Failed to update user in Keycloak: {str(e)}")
    
    async def update_user(
        self,
        user_id: int,
        user_data: UserBase
    ) -> User:
        """Обновление пользователя в локальной БД и Keycloak (только базовые поля)"""
        user = await self.get_user_by_id(user_id)
        
        # Проверяем, что пользователь активен
        if not user.is_active:
            raise ValidationException("Cannot update inactive user")
        
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
        
        # КОПИРУЕМ старые значения для возможного отката
        old_values = {}
        for field in ['email', 'username', 'first_name', 'last_name']:
            old_values[field] = getattr(user, field, None)
        
        try:
            # Применяем обновления к локальному пользователю
            for field, value in update_data.items():
                if field in ['email', 'username']:
                    value = value.lower()
                setattr(user, field, value)
            
            # ОБНОВЛЯЕМ: Сначала обновляем в Keycloak, потом в локальной БД
            if update_data:
                self._update_user_in_keycloak(
                    user.keycloak_id, 
                    update_data,  # Теперь включаем username
                    None  # Роли не обновляем в этом методе
                )
            
            # Обновляем в локальной БД
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            return user
            
        except Exception as e:
            # ВОССТАНАВЛИВАЕМ старые значения в объекте перед откатом
            for field, value in old_values.items():
                if value is not None:
                    setattr(user, field, value)
            
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise DatabaseException(f"Failed to update user: {str(e)}")
    
    async def delete_user(self, user_id: int) -> bool:
        """ПОЛНОЕ УДАЛЕНИЕ пользователя из локальной БД и Keycloak"""
        user = await self.get_user_by_id(user_id)
        
        # Сохраняем данные для возможного восстановления
        user_data = {
            'id': user.id,
            'keycloak_id': user.keycloak_id,
            'username': user.username,
            'email': user.email
        }
        
        try:
            # Сначала удаляем из Keycloak
            try:
                self.kc.delete_user(user.keycloak_id)
                logger.info(f"User {user.keycloak_id} deleted from Keycloak")
            except Exception as kc_error:
                logger.error(f"Failed to delete user {user.keycloak_id} from Keycloak: {kc_error}")
                raise DatabaseException(f"Failed to delete user from Keycloak: {str(kc_error)}")
            
            # Затем удаляем из локальной БД
            await self.db.delete(user)
            await self.db.commit()
            
            logger.info(f"User {user_id} deleted completely")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            # Восстановление в Keycloak сложнее, поэтому просто логируем ошибку
            if isinstance(e, DatabaseException) and "Keycloak" in str(e):
                logger.critical(f"User {user_data['keycloak_id']} deleted from Keycloak but not from local DB. Manual intervention required.")
            
            raise DatabaseException(f"Failed to delete user: {str(e)}")
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        role: Optional[UserRole] = None
    ) -> Tuple[List[User], int]:
        """Получение списка пользователей с пагинацией"""
        query = select(User)
        
        # Применяем фильтры
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if role is not None:
            # Фильтрация по роли через join с таблицей ролей
            query = query.join(UserRoleAssignment).where(UserRoleAssignment.role == role)
        
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
    
    async def toggle_user_status(self, user_id: int) -> User:
        """Переключение статуса активности пользователя"""
        user = await self.get_user_by_id(user_id)
        
        # Сохраняем старое значение для отката
        old_status = user.is_active
        
        try:
            # Меняем статус в локальной БД
            new_status = not user.is_active
            user.is_active = new_status
            
            # Обновляем статус в Keycloak
            try:
                self.kc.admin.update_user(user.keycloak_id, {"enabled": new_status})
                logger.info(f"User {user.keycloak_id} status in Keycloak changed to {new_status}")
            except Exception as kc_error:
                logger.error(f"Failed to update user status in Keycloak: {kc_error}")
                raise DatabaseException(f"Failed to update user status in Keycloak: {str(kc_error)}")
            
            # Сохраняем изменения в локальной БД
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User {user_id} status changed to {user.is_active}")
            return user
            
        except Exception as e:
            # Восстанавливаем старое значение
            user.is_active = old_status
            await self.db.rollback()
            logger.error(f"Failed to toggle user status {user_id}: {e}")
            raise DatabaseException(f"Failed to change user status: {str(e)}")
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Получение пользователей по роли"""
        stmt = select(User).join(UserRoleAssignment).where(UserRoleAssignment.role == role)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_user_roles(self, user_id: int, roles_data: UserRolesUpdate) -> User:
        """Обновление ролей пользователя"""
        user = await self.get_user_by_id(user_id)
        
        # Сохраняем старые роли для отката
        old_roles = user.roles.copy()
        
        try:
            # Удаляем старые роли
            stmt = delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            await self.db.execute(stmt)
            
            # Добавляем новые роли
            for role in roles_data.roles:
                role_assignment = UserRoleAssignment(
                    user_id=user_id,
                    role=role
                )
                self.db.add(role_assignment)
            
            # Обновляем роли в Keycloak
            try:
                self.kc.update_user_in_keycloak(
                    keycloak_id=user.keycloak_id,
                    user_data=None,
                    roles=[role.value for role in roles_data.roles]
                )
                logger.info(f"User {user.keycloak_id} roles updated in Keycloak: {[role.value for role in roles_data.roles]}")
            except Exception as kc_error:
                logger.error(f"Failed to update roles in Keycloak: {kc_error}")
                raise DatabaseException(f"Failed to update roles in Keycloak: {str(kc_error)}")
            
            # Сохраняем изменения в локальной БД
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Roles updated for user {user_id}")
            return user
            
        except Exception as e:
            # Восстанавливаем старые роли
            # Нужно удалить все назначенные роли и восстановить старые
            stmt = delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            await self.db.execute(stmt)
            
            for role in old_roles:
                role_assignment = UserRoleAssignment(
                    user_id=user_id,
                    role=role
                )
                self.db.add(role_assignment)
            
            await self.db.rollback()
            logger.error(f"Failed to update roles for user {user_id}: {e}")
            raise DatabaseException(f"Failed to update user roles: {str(e)}")
    
    async def get_my_info(self, user_id: int) -> dict:
        """Получение информации о текущем пользователе"""
        user = await self.get_user_by_id(user_id)
        
        return {
            "id": user.id,
            "keycloak_id": user.keycloak_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "is_active": user.is_active,
            "created_at": user.created_at
        }