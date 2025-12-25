import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func
from typing import Any, Dict, Optional, List, Tuple

from app.database.models import User, UserRoleAssignment
from shared.schemas.shared import UserRole
from app.schemas.user import UserBase, UserRolesUpdate
from app.services.keycloak_client import KeycloakClient
from app.services.event_service import get_event_service
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
        self.event_service = get_event_service()

    async def create_user_profile(self, data) -> User:
        """Создание профиля пользователя (вызвано из auth-service через события)"""
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
            
            # Публикуем событие создания профиля
            await self.event_service.publish_user_profile_created(
                keycloak_id=new_user.keycloak_id,
                user_id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                roles=[data.role.value]
            )
            logger.info(f"User profile created event published for {new_user.id}")
            
            return new_user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"DB Error creating user profile: {e}")
            raise DatabaseException("Failed to create user profile")

    async def update_user(
        self,
        user_id: int,
        user_data: UserBase,
        current_user: dict,
        source_service: str = "api"
    ) -> User:
        """Обновление пользователя с гибридным подходом"""
        user = await self.get_user_by_id(user_id)
        
        # Проверяем права: либо свой профиль, либо админ
        is_self = user_id == current_user["id"]
        is_admin = UserRole.ADMIN in current_user["roles"]
        
        if not (is_self or is_admin):
            raise PermissionDeniedException("Not enough permissions")
        
        if not user.is_active:
            raise ValidationException("Cannot update inactive user")
        
        # Сохраняем старые значения
        old_values = {}
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field in ['email', 'username', 'first_name', 'last_name']:
            if field in update_data:
                old_values[field] = getattr(user, field)
        
        # Проверяем уникальность email и username
        if 'email' in update_data or 'username' in update_data:
            conditions = []
            if 'email' in update_data and update_data['email'].lower() != user.email:
                conditions.append(User.email == update_data['email'].lower())
            if 'username' in update_data and update_data['username'].lower() != user.username:
                conditions.append(User.username == update_data['username'].lower())
            
            if conditions:
                stmt = select(User).where(or_(*conditions), User.id != user_id)
                result = await self.db.execute(stmt)
                if result.scalar_one_or_none():
                    raise UserAlreadyExistsException("Email or username already taken")
        
        # Если обновление инициировано из API, используем гибридный подход
        if source_service == "api":
            try:
                # 1. Сначала обновляем локальную БД
                for field, value in update_data.items():
                    if field in ['email', 'username']:
                        value = value.lower()
                    setattr(user, field, value)
                
                await self.db.commit()
                await self.db.refresh(user)
                
                # 2. Отправляем запрос на обновление в auth-service через RabbitMQ
                correlation_id = str(uuid.uuid4())
                logger.info(f"Requesting profile update for user {user_id} (correlation: {correlation_id})")
                
                success = await self.event_service.publish_user_profile_update_requested(
                    keycloak_id=user.keycloak_id,
                    user_id=user.id,
                    updated_fields=update_data,
                    old_values=old_values,
                    correlation_id=correlation_id
                )
                
                if not success:
                    # Если не удалось опубликовать событие, откатываем изменения
                    await self.db.rollback()
                    # Восстанавливаем объект из базы
                    await self.db.refresh(user)
                    logger.error(f"Failed to send update request to auth-service for user {user_id}")
                    raise DatabaseException("Failed to send update request to auth-service")
                
                logger.info(f"User {user_id} updated locally, request sent to auth-service")
                return user
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to update user {user_id}: {e}")
                raise DatabaseException("Failed to update user")
        
        # Если источник события - auth-service (подтверждение), обновляем локально
        elif source_service == "auth-service":
            try:
                # Обновляем локальную БД
                for field, value in update_data.items():
                    if field in ['email', 'username']:
                        value = value.lower()
                    setattr(user, field, value)
                
                await self.db.commit()
                await self.db.refresh(user)
                
                logger.info(f"User {user_id} updated locally from auth-service")
                return user
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to update user {user_id} locally: {e}")
                raise DatabaseException("Failed to update user locally")
        
        # Для обновлений из других источников
        else:
            raise ValidationException(f"Unknown source service: {source_service}")
        
        return user

    async def toggle_user_status(self, user_id: int, current_user: dict) -> User:
        """Переключение статуса активности пользователя с гибридным подходом"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Сохраняем старое значение для возможного отката
        old_status = user.is_active
        new_status = not old_status
        
        try:
            # 1. Обновляем в локальной БД user-service
            user.is_active = new_status
            await self.db.commit()
            await self.db.refresh(user)
            
            # 2. Публикуем запрос на обновление статуса в Keycloak через auth-service
            correlation_id = str(uuid.uuid4())
            logger.info(f"Requesting status change for user {user_id} to {new_status} (correlation: {correlation_id})")
            
            success = await self.event_service.publish_user_status_change_requested(
                keycloak_id=user.keycloak_id,
                user_id=user.id,
                is_active=new_status,
                reason="admin_action",
                correlation_id=correlation_id
            )
            
            if not success:
                # Если не удалось опубликовать событие, откатываем изменения
                await self.db.rollback()
                # Восстанавливаем объект из базы
                await self.db.refresh(user)
                logger.error(f"Failed to send status change request to auth-service for user {user_id}")
                raise DatabaseException("Failed to send status change request to auth-service")
            
            logger.info(f"User {user_id} status changed locally to {new_status}, request sent to auth-service")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to toggle user status {user_id}: {e}")
            raise DatabaseException("Failed to change user status")

    async def update_user_roles(
        self,
        user_id: int,
        roles_data: UserRolesUpdate,
        current_user: dict
    ) -> User:
        """Обновление ролей пользователя с гибридным подходом"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Сохраняем старые роли
        old_roles = [role.value for role in user.roles]
        new_roles = [role.value for role in roles_data.roles]
        
        try:
            # 1. Обновляем роли в локальной БД user-service
            # Удаляем старые роли
            await self.db.execute(
                delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            )
            
            # Добавляем новые роли
            for role in roles_data.roles:
                role_assignment = UserRoleAssignment(
                    user_id=user_id,
                    role=role
                )
                self.db.add(role_assignment)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            # 2. Отправляем запрос на обновление ролей в auth-service
            correlation_id = str(uuid.uuid4())
            logger.info(f"Requesting roles update for user {user_id} (correlation: {correlation_id})")
            
            success = await self.event_service.publish_user_roles_update_requested(
                keycloak_id=user.keycloak_id,
                user_id=user.id,
                roles=new_roles,
                old_roles=old_roles,
                correlation_id=correlation_id
            )
            
            if not success:
                # Если не удалось опубликовать событие, откатываем изменения
                await self.db.rollback()
                # Восстанавливаем объект из базы
                await self.db.refresh(user)
                logger.error(f"Failed to send roles update request to auth-service for user {user_id}")
                raise DatabaseException("Failed to send roles update request to auth-service")
            
            logger.info(f"User {user_id} roles updated locally, request sent to auth-service")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update roles for user {user_id}: {e}")
            raise DatabaseException("Failed to update user roles")

    async def delete_user(self, user_id: int, current_user: dict) -> bool:
        """Удаление пользователя с гибридным подходом"""
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        user = await self.get_user_by_id(user_id)
        
        try:
            # 1. Удаляем пользователя из локальной БД user-service
            await self.db.delete(user)
            await self.db.commit()
            
            # 2. Отправляем запрос на удаление в auth-service
            correlation_id = str(uuid.uuid4())
            logger.info(f"Requesting deletion for user {user_id} (correlation: {correlation_id})")
            
            success = await self.event_service.publish_user_deletion_requested(
                keycloak_id=user.keycloak_id,
                user_id=user.id,
                correlation_id=correlation_id
            )
            
            if not success:
                # Если не удалось опубликовать событие, откатываем изменения
                # Но удаление нельзя откатить так просто - это необратимая операция
                # Поэтому здесь нужно вернуть ошибку, но пользователь уже удален локально
                logger.error(f"Failed to send deletion request to auth-service, but user {user_id} already deleted locally")
                # Пользователь уже удален, возвращаем успех для клиента
                # Но логируем проблему
                return True
            
            logger.info(f"User {user_id} deleted locally, request sent to auth-service")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise DatabaseException("Failed to delete user")

    async def update_user_from_event(
        self,
        keycloak_id: str,
        updated_fields: Dict[str, Any],
        source_service: str = "auth-service"
    ) -> bool:
        """Обновление пользователя из события (подтверждение от auth-service)"""
        user = await self.get_user_by_keycloak_id(keycloak_id)
        if not user:
            logger.warning(f"User {keycloak_id} not found in user-service")
            return False
        
        try:
            # Обновляем только разрешенные поля
            allowed_fields = ["email", "first_name", "last_name", "username", "is_active"]
            fields_to_update = {
                k: v for k, v in updated_fields.items() 
                if k in allowed_fields and v is not None
            }
            
            if not fields_to_update:
                logger.debug(f"No relevant fields to update for {keycloak_id}")
                return True
            
            # Проверяем, нужно ли вообще обновлять
            needs_update = False
            for field, new_value in fields_to_update.items():
                current_value = getattr(user, field)
                if field in ['email', 'username'] and isinstance(new_value, str):
                    new_value = new_value.lower()
                if current_value != new_value:
                    needs_update = True
                    break
            
            if not needs_update:
                logger.debug(f"User {keycloak_id} already has updated values, skipping")
                return True
            
            # Обновляем поля
            for field, value in fields_to_update.items():
                if field in ['email', 'username']:
                    value = value.lower()
                setattr(user, field, value)
            
            await self.db.commit()
            logger.info(f"User {keycloak_id} updated from {source_service} confirmation: {list(fields_to_update.keys())}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {keycloak_id} from event: {e}")
            return False

    async def check_user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя по ID"""
        try:
            user = await self.get_user_by_id(user_id)
            return True
        except UserNotFoundException:
            return False

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