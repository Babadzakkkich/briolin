import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete, or_
from typing import Any, Dict, List, Optional, Tuple

from app.database.models import User, UserRoleAssignment
from shared.schemas.shared import UserRole
from app.schemas.user import UserBase, UserRolesUpdate
from app.services.keycloak_client import KeycloakClient
from app.services.event_service import get_event_service
from app.services.event_waiter import get_event_waiter
from app.services.saga_service import get_user_saga_service
from app.core.exceptions import (
    UserAlreadyExistsException, 
    UserNotFoundException,
    DatabaseException,
    ValidationException,
    PermissionDeniedException
)
from app.core.logger import logger


class UserService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.event_service = get_event_service()
        self.event_waiter = get_event_waiter()
        self.saga_service = get_user_saga_service()

    async def create_user_profile(self, data) -> User:
        """Создание профиля пользователя через SAGA транзакцию"""
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_profile_creation_saga(
            keycloak_id=data.keycloak_id,
            email=data.email,
            username=data.username,
            role=data.role.value
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        for _ in range(30):
            await asyncio.sleep(1)
            status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
            
            if status["status"] in ["completed", "compensated", "failed"]:
                break
        
        final_status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
        
        if final_status["status"] == "completed":
            # Получаем ID пользователя из результатов SAGA
            user_id = final_status["results"]["create_user_profile"]["result"]["user_id"]
            
            # Получаем пользователя из БД
            user = await self.get_user_by_id(user_id)
            
            logger.info(f"User profile created via SAGA: {user.id}")
            return user
            
        elif final_status["status"] == "compensated":
            raise DatabaseException("User profile creation failed and was compensated")
        else:
            raise DatabaseException(f"User profile creation failed: {final_status.get('error')}")

    async def update_user(
        self,
        user_id: int,
        user_data: UserBase,
        current_user: dict,
        source_service: str = "api"
    ) -> User:
        """Обновление пользователя с ожиданием подтверждения от auth-service"""
        user = await self.get_user_by_id(user_id)
        
        # Проверяем права
        is_self = user_id == current_user["id"]
        is_admin = UserRole.ADMIN in current_user["roles"]
        
        if not (is_self or is_admin):
            raise PermissionDeniedException("Not enough permissions")
        
        if not user.is_active:
            raise ValidationException("Cannot update inactive user")
        
        # Сохраняем старые значения
        old_values = {}
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field in ['email', 'username']:
            if field in update_data:
                old_values[field] = getattr(user, field)
        
        # Проверяем уникальность
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
        
        if source_service == "api":
            # Генерируем correlation_id для отслеживания
            correlation_id = str(uuid.uuid4())
            
            # 1. Отправляем запрос на обновление в auth-service
            success = await self.event_service.publish_user_profile_update_requested(
                keycloak_id=user.keycloak_id,
                user_id=user.id,
                updated_fields=update_data,
                old_values=old_values,
                correlation_id=correlation_id
            )
            
            if not success:
                raise DatabaseException("Failed to send update request to auth-service")
            
            logger.info(f"Sent update request for user {user_id} with correlation {correlation_id}")
            
            # 2. Ждем подтверждения от auth-service через EventWaiter
            result = await self.event_waiter.wait_for_event(correlation_id, timeout=30)
            
            if not result:
                raise DatabaseException("Timeout waiting for update confirmation from auth-service")
            
            if result.get("status") != "success":
                error_msg = result.get("error", "Unknown error from auth-service")
                raise DatabaseException(f"Update failed in auth-service: {error_msg}")
            
            # 3. Обновляем локальную БД (уже должно быть сделано в обработчике события)
            # Но для надежности обновляем еще раз
            await self.update_user_from_event(
                keycloak_id=user.keycloak_id,
                updated_fields=update_data,
                source_service="self"
            )
            
            # 4. Возвращаем обновленного пользователя
            return await self.get_user_by_id(user_id)
        
        elif source_service == "auth-service":
            # Это вызов из обработчика событий
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
        
        else:
            raise ValidationException(f"Unknown source service: {source_service}")

    async def toggle_user_status(self, user_id: int, current_user: dict) -> User:
        """Переключение статуса активности пользователя с ожиданием подтверждения"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Генерируем correlation_id
        correlation_id = str(uuid.uuid4())
        new_status = not user.is_active
        
        # 1. Отправляем запрос на обновление статуса в auth-service
        success = await self.event_service.publish_user_status_change_requested(
            keycloak_id=user.keycloak_id,
            user_id=user.id,
            is_active=new_status,
            reason="admin_action",
            correlation_id=correlation_id
        )
        
        if not success:
            raise DatabaseException("Failed to send status change request to auth-service")
        
        logger.info(f"Sent status change request for user {user_id} with correlation {correlation_id}")
        
        # 2. Ждем подтверждения от auth-service
        result = await self.event_waiter.wait_for_event(correlation_id, timeout=30)
        
        if not result:
            raise DatabaseException("Timeout waiting for status change confirmation from auth-service")
        
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error from auth-service")
            raise DatabaseException(f"Status change failed in auth-service: {error_msg}")
        
        # 3. Обновляем локальную БД (уже должно быть сделано в обработчике события)
        await self.update_user_from_event(
            keycloak_id=user.keycloak_id,
            updated_fields={"is_active": new_status},
            source_service="self"
        )
        
        # 4. Возвращаем обновленного пользователя
        return await self.get_user_by_id(user_id)

    async def update_user_roles(
        self,
        user_id: int,
        roles_data: UserRolesUpdate,
        current_user: dict
    ) -> User:
        """Обновление ролей пользователя с ожиданием подтверждения"""
        user = await self.get_user_by_id(user_id)
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        # Сохраняем старые роли
        old_roles = [role.value for role in user.roles]
        new_roles = [role.value for role in roles_data.roles]
        
        # Генерируем correlation_id
        correlation_id = str(uuid.uuid4())
        
        # 1. Отправляем запрос на обновление ролей в auth-service
        success = await self.event_service.publish_user_roles_update_requested(
            keycloak_id=user.keycloak_id,
            user_id=user.id,
            roles=new_roles,
            old_roles=old_roles,
            correlation_id=correlation_id
        )
        
        if not success:
            raise DatabaseException("Failed to send roles update request to auth-service")
        
        logger.info(f"Sent roles update request for user {user_id} with correlation {correlation_id}")
        
        # 2. Ждем подтверждения от auth-service
        result = await self.event_waiter.wait_for_event(correlation_id, timeout=30)
        
        if not result:
            raise DatabaseException("Timeout waiting for roles update confirmation from auth-service")
        
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error from auth-service")
            raise DatabaseException(f"Roles update failed in auth-service: {error_msg}")
        
        # 3. Обновляем локальную БД
        await self.db.execute(
            delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
        )
        
        for role in roles_data.roles:
            role_assignment = UserRoleAssignment(
                user_id=user_id,
                role=role
            )
            self.db.add(role_assignment)
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User {user_id} roles updated locally after confirmation")
            
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user roles locally: {e}")
            raise DatabaseException("Failed to update user roles locally")

    async def delete_user(self, user_id: int, current_user: dict) -> bool:
        """Удаление пользователя с ожиданием подтверждения"""
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        user = await self.get_user_by_id(user_id)
        
        # Генерируем correlation_id
        correlation_id = str(uuid.uuid4())
        
        # 1. Отправляем запрос на удаление в auth-service
        success = await self.event_service.publish_user_deletion_requested(
            keycloak_id=user.keycloak_id,
            user_id=user.id,
            correlation_id=correlation_id
        )
        
        if not success:
            raise DatabaseException("Failed to send deletion request to auth-service")
        
        logger.info(f"Sent deletion request for user {user_id} with correlation {correlation_id}")
        
        # 2. НЕ УДАЛЯЕМ пользователя локально здесь - дождемся подтверждения
        # Вместо этого просто регистрируем ожидание
        
        # 3. Ждем подтверждения от auth-service
        result = await self.event_waiter.wait_for_event(correlation_id, timeout=30)
        
        if not result:
            raise DatabaseException("Timeout waiting for deletion confirmation from auth-service")
        
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error from auth-service")
            raise DatabaseException(f"Deletion failed in auth-service: {error_msg}")
        
        # 4. После подтверждения проверяем, не был ли пользователь уже удален обработчиком события
        # Если не был - удаляем здесь
        user_still_exists = await self.check_user_exists(user_id)
        
        if user_still_exists:
            try:
                # Получаем пользователя снова (объект мог быть отсоединен)
                user_to_delete = await self.get_user_by_id(user_id)
                await self.db.delete(user_to_delete)
                await self.db.commit()
                
                logger.info(f"User {user_id} deleted locally after confirmation")
                return True
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to delete user {user_id} locally: {e}")
                raise DatabaseException("Failed to delete user locally")
        else:
            logger.info(f"User {user_id} was already deleted by event handler")
            return True

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
            allowed_fields = ["email", "username", "is_active"]
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
            await self.db.refresh(user)  # Обновляем объект после коммита
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
            "roles": user.roles,
            "is_active": user.is_active,
            "is_test_passed": user.is_test_passed,
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
                    User.email.ilike(search_term)
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