from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func
from typing import Any, Dict, Optional, List, Tuple

from app.database.models import User, UserRoleAssignment
from shared.schemas.shared import UserRole
from app.schemas.user import UserBase, UserRolesUpdate
from app.services.keycloak_client import KeycloakClient
from app.services.auth_service_client import get_auth_service_client
from app.core.exceptions import (
    UserAlreadyExistsException, 
    UserNotFoundException,
    DatabaseException,
    ValidationException,
    PermissionDeniedException,
    KeycloakConnectionError
)
from app.core.logger import logger

class UserService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.auth_client = get_auth_service_client()  # Добавляем клиент для auth-service

    async def update_user(
        self,
        user_id: int,
        user_data: UserBase,
        current_user: dict
    ) -> User:
        """Обновление пользователя в локальной БД, auth-service и Keycloak"""
        user = await self.get_user_by_id(user_id)
        
        # Проверяем права: либо свой профиль, либо админ
        is_self = user_id == current_user["id"]
        is_admin = UserRole.ADMIN in current_user["roles"]
        
        if not (is_self or is_admin):
            raise PermissionDeniedException("Not enough permissions")
        
        if not user.is_active:
            raise ValidationException("Cannot update inactive user")
        
        # Сохраняем старые значения
        old_email = user.email
        old_username = user.username
        old_first_name = user.first_name
        old_last_name = user.last_name
        
        # Проверяем уникальность
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
        
        try:
            # 1. Обновляем в локальной БД user-service
            for field, value in update_data.items():
                if field in ['email', 'username']:
                    value = value.lower()
                setattr(user, field, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            # 2. Если изменился email, обновляем в auth-service
            update_auth_data = {}
            if 'email' in update_data:
                update_auth_data['email'] = user.email
            
            if update_auth_data:
                try:
                    await self.auth_client.update_user_in_auth_service(
                        user.keycloak_id, 
                        update_auth_data
                    )
                except Exception as e:
                    logger.error(f"Failed to update user in auth-service: {e}")
                    # Откатываем локальные изменения
                    await self.db.rollback()
                    raise DatabaseException("User updated locally but failed to update in auth-service")
            
            # 3. Обновляем в Keycloak
            try:
                kc_data = {}
                if 'email' in update_data:
                    kc_data['email'] = user.email
                if 'username' in update_data:
                    kc_data['username'] = user.username
                if 'first_name' in update_data:
                    kc_data['first_name'] = user.first_name
                if 'last_name' in update_data:
                    kc_data['last_name'] = user.last_name
                
                if kc_data:
                    self.kc.update_user_in_keycloak(user.keycloak_id, kc_data)
            except KeycloakConnectionError as e:
                logger.error(f"Failed to update user in Keycloak: {e}")
                # Откатываем локальные изменения и auth-service
                if 'email' in update_data:
                    user.email = old_email
                    try:
                        await self.auth_client.update_user_in_auth_service(
                            user.keycloak_id,
                            {'email': old_email}
                        )
                    except Exception as rollback_error:
                        logger.error(f"Failed to rollback email in auth-service: {rollback_error}")
                
                await self.db.commit()
                raise DatabaseException("User updated locally and in auth-service but failed in Keycloak")
            
            logger.info(f"User {user_id} updated successfully in all systems (DB, auth-service, Keycloak)")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise DatabaseException("Failed to update user")

    async def delete_user(self, user_id: int, current_user: dict) -> bool:
        """ПОЛНОЕ УДАЛЕНИЕ пользователя из всех систем"""
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        user = await self.get_user_by_id(user_id)
        
        try:
            # 1. Удаляем из Keycloak
            try:
                self.kc.delete_user_from_keycloak(user.keycloak_id)
            except KeycloakConnectionError as e:
                logger.error(f"Failed to delete user from Keycloak: {e}")
                raise DatabaseException("Cannot delete user from Keycloak")
            
            # 2. Удаляем из auth-service
            try:
                await self.auth_client.delete_user_from_auth_service(user.keycloak_id)
            except Exception as e:
                logger.error(f"Failed to delete user from auth-service: {e}")
                # Пытаемся восстановить пользователя в Keycloak
                try:
                    # Создаем пользователя заново в Keycloak
                    self.kc.admin.create_user({
                        "username": user.username,
                        "email": user.email,
                        "firstName": user.first_name,
                        "lastName": user.last_name,
                        "enabled": False,
                        "emailVerified": False
                    })
                    logger.warning(f"Recreated user {user.keycloak_id} in Keycloak after auth-service failure")
                except Exception as restore_error:
                    logger.critical(f"Failed to restore user in Keycloak: {restore_error}")
                
                raise DatabaseException("User deleted from Keycloak but failed in auth-service")
            
            # 3. Удаляем из локальной БД user-service
            await self.db.delete(user)
            await self.db.commit()
            
            logger.info(f"User {user_id} deleted completely from all systems (Keycloak, auth-service, DB)")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise DatabaseException("Failed to delete user")

    async def toggle_user_status(self, user_id: int, current_user: dict) -> User:
        """Переключение статуса активности пользователя во всех системах"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Сохраняем старое значение
        old_status = user.is_active
        
        try:
            new_status = not user.is_active
            user.is_active = new_status
            
            # 1. Обновляем в локальной БД user-service
            await self.db.commit()
            await self.db.refresh(user)
            
            # 2. Обновляем статус в auth-service
            try:
                await self.auth_client.update_user_in_auth_service(
                    user.keycloak_id,
                    {"is_active": new_status}
                )
            except Exception as e:
                logger.error(f"Failed to update user status in auth-service: {e}")
                # Откатываем локальное изменение
                user.is_active = old_status
                await self.db.commit()
                raise DatabaseException("User status updated locally but failed in auth-service")
            
            # 3. Обновляем статус в Keycloak
            try:
                self.kc.update_user_status_in_keycloak(user.keycloak_id, new_status)
            except KeycloakConnectionError as e:
                logger.error(f"Failed to update user status in Keycloak: {e}")
                # Откатываем локальное изменение и auth-service
                user.is_active = old_status
                await self.db.commit()
                try:
                    await self.auth_client.update_user_in_auth_service(
                        user.keycloak_id,
                        {"is_active": old_status}
                    )
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback status in auth-service: {rollback_error}")
                
                raise DatabaseException("User status updated locally and in auth-service but failed in Keycloak")
            
            logger.info(f"User {user_id} status changed to {user.is_active} in all systems")
            return user
            
        except Exception as e:
            user.is_active = old_status
            await self.db.rollback()
            logger.error(f"Failed to toggle user status {user_id}: {e}")
            raise DatabaseException("Failed to change user status")
    
    async def update_user_roles(
        self,
        user_id: int,
        roles_data: UserRolesUpdate,
        current_user: dict
    ) -> User:
        """Обновление ролей пользователя в локальной БД и Keycloak"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Сохраняем старые роли для отката
        old_roles = user.roles.copy()
        
        try:
            # 1. Удаляем старые роли из локальной БД
            stmt = delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            await self.db.execute(stmt)
            
            # 2. Добавляем новые роли в локальную БД
            for role in roles_data.roles:
                role_assignment = UserRoleAssignment(
                    user_id=user_id,
                    role=role
                )
                self.db.add(role_assignment)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            # 3. Обновляем роли в Keycloak
            try:
                # Преобразуем роли в строки
                role_strings = [role.value for role in roles_data.roles]
                self.kc.update_user_roles_in_keycloak(user.keycloak_id, role_strings)
            except KeycloakConnectionError as e:
                logger.error(f"Failed to update user roles in Keycloak: {e}")
                # Откатываем локальные изменения
                await self.db.rollback()
                # Восстанавливаем старые роли
                stmt = delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
                await self.db.execute(stmt)
                for role in old_roles:
                    role_assignment = UserRoleAssignment(
                        user_id=user_id,
                        role=role
                    )
                    self.db.add(role_assignment)
                await self.db.commit()
                await self.db.refresh(user)
                raise DatabaseException("Roles updated locally but failed in Keycloak")
            
            logger.info(f"Roles updated for user {user_id} in both DB and Keycloak")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update roles for user {user_id}: {e}")
            raise DatabaseException("Failed to update user roles")

    async def check_user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя по ID"""
        try:
            user = await self.get_user_by_id(user_id)
            return True
        except UserNotFoundException:
            return False

    # Остальные методы остаются без изменений
    async def create_user_profile(self, data) -> User:
        """Создание профиля пользователя (вызвано из auth-service)"""
        # Проверяем уникальность
        stmt = select(User).where(
            (User.email == data.email) | (User.username == data.username)
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException("Email or username already exists")
        
        # Создаем пользователя
        new_user = User(
            keycloak_id=data.keycloak_id,
            username=data.username,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
        )
        
        # Добавляем роль
        role_assignment = UserRoleAssignment(user=new_user, role=data.role)
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            logger.info(f"User profile created: {new_user.id} with role {data.role}")
            return new_user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"DB Error creating user profile: {e}")
            raise DatabaseException("Failed to create user profile")

    async def get_user_by_id(self, user_id: int) -> User:
        """Получение пользователя по ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundException(f"User with id {user_id} not found")
        return user

    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Получение пользователя по Keycloak ID"""
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_my_info(self, user_id: int) -> Dict[str, Any]:
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

    async def list_users(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None,
                        search: Optional[str] = None, role: Optional[UserRole] = None) -> Tuple[List[User], int]:
        """Получение списка пользователей с фильтрацией"""
        query = select(User)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        if role:
            query = query.join(UserRoleAssignment).where(UserRoleAssignment.role == role)
        
        # Получаем общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Получаем данные с пагинацией
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Получение пользователей по роли"""
        stmt = select(User).join(UserRoleAssignment).where(UserRoleAssignment.role == role)
        result = await self.db.execute(stmt)
        return result.scalars().all()