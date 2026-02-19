import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete, or_
from typing import Any, Dict, List, Optional, Tuple

from app.database.models import User, UserRoleAssignment
from shared.schemas.shared import UserRole
from app.schemas.user import UserBase, UserRolesUpdate
from app.services.keycloak_client import KeycloakClient
from app.services.saga_worker import get_saga_worker
from app.core.exceptions import (
    UserAlreadyExistsException, 
    UserNotFoundException,
    DatabaseException,
    ValidationException,
    PermissionDeniedException
)
from app.core.logger import logger
from shared.saga.models import SagaInstance, SagaStatus


def _filter_dependencies(deps: List[Optional[str]]) -> Optional[List[str]]:
    """
    Фильтрует список зависимостей, удаляя None значения.
    Возвращает None если после фильтрации список пуст.
    """
    filtered = [dep for dep in deps if dep is not None]
    return filtered if filtered else None


class UserService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.saga_worker = get_saga_worker()

    # ========== СОЗДАНИЕ ПРОФИЛЯ ==========
    
    async def create_user_profile(self, data) -> Dict[str, Any]:
        """АСИНХРОННОЕ создание профиля пользователя через SAGA"""
        
        # Проверяем, не существует ли уже пользователь
        stmt = select(User).where(
            or_(
                User.keycloak_id == data.keycloak_id,
                User.email == data.email,
                User.username == data.username
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            if existing.keycloak_id == data.keycloak_id:
                logger.info(f"User already exists: {data.keycloak_id}")
                return {
                    "status": "success",
                    "user": existing,
                    "already_exists": True
                }
            else:
                raise UserAlreadyExistsException("Email or username already taken")
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Создание в user-db
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_creation",
            step_name="create_user_profile",
            event_type="saga.step.create_user_profile",
            payload={
                "keycloak_id": data.keycloak_id,
                "email": data.email,
                "username": data.username,
                "role": data.role.value if hasattr(data.role, 'value') else data.role
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Назначение роли (зависит от первого шага)
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_creation",
            step_name="assign_user_role",
            event_type="saga.step.assign_user_role",
            payload={
                "role": data.role.value if hasattr(data.role, 'value') else data.role
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "create_user_profile"
            }
        )
        
        # Шаг 3: Публикация USER_PROFILE_CREATED (зависит от первого шага)
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_creation",
            step_name="publish_user_profile_created",
            event_type="saga.step.publish_user_profile_created",
            payload={
                "role": data.role.value if hasattr(data.role, 'value') else data.role
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "create_user_profile"
            }
        )
        
        logger.info(f"User profile creation initiated for {data.keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "User profile creation initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/users/saga/{saga_id}/status"
        }
    
    # ========== ОБНОВЛЕНИЕ ПРОФИЛЯ ==========
    
    async def update_user(
        self,
        keycloak_id: str,
        user_data: UserBase,
        current_user: dict
    ) -> Dict[str, Any]:
        """АСИНХРОННОЕ обновление пользователя через SAGA"""
        user = await self.get_user_by_keycloak_id(keycloak_id)
        
        if not user:
            raise UserNotFoundException(f"User with keycloak_id {keycloak_id} not found")
        
        # Проверяем права
        is_self = keycloak_id == current_user["keycloak_id"]
        is_admin = UserRole.ADMIN in current_user["roles"]
        
        if not (is_self or is_admin):
            raise PermissionDeniedException("Not enough permissions")
        
        if not user.is_active:
            raise ValidationException("Cannot update inactive user")
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return {
                "status": "success",
                "message": "No data to update",
                "user": user
            }
        
        # Проверяем уникальность
        if 'email' in update_data or 'username' in update_data:
            conditions = []
            if 'email' in update_data and update_data['email'].lower() != user.email:
                conditions.append(User.email == update_data['email'].lower())
            if 'username' in update_data and update_data['username'].lower() != user.username:
                conditions.append(User.username == update_data['username'].lower())
            
            if conditions:
                stmt = select(User).where(or_(*conditions), User.id != user.id)
                result = await self.db.execute(stmt)
                if result.scalar_one_or_none():
                    raise UserAlreadyExistsException("Email or username already taken")
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Отправляем запрос в auth-service (публикация события)
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_update",
            step_name="publish_user_profile_update_requested",
            event_type="saga.step.publish_user_profile_update_requested",
            payload={
                "keycloak_id": user.keycloak_id,
                "user_id": user.id,
                "updated_fields": update_data,
                "old_values": {}
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Обновление в user-db
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_update",
            step_name="update_user_profile",
            event_type="saga.step.update_user_profile",
            payload={
                "keycloak_id": keycloak_id,
                "update_data": update_data
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 3: Публикация подтверждения обновления (после обновления в user-db)
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_profile_update",
            step_name="publish_user_updated",
            event_type="saga.step.publish_user_updated",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "updated_fields": update_data,
                "source_service": "user-service"
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "update_user_profile"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"User update initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "User update initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/users/saga/{saga_id}/status"
        }

    # ========== ИЗМЕНЕНИЕ СТАТУСА ==========
    
    async def toggle_user_status(self, keycloak_id: str, current_user: dict) -> Dict[str, Any]:
        """АСИНХРОННОЕ переключение статуса пользователя"""
        user = await self.get_user_by_keycloak_id(keycloak_id)
        
        if not user:
            raise UserNotFoundException(f"User with keycloak_id {keycloak_id} not found")
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        new_status = not user.is_active
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Отправляем запрос в auth-service
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="publish_user_status_change_requested",
            event_type="saga.step.publish_user_status_change_requested",
            payload={
                "keycloak_id": user.keycloak_id,
                "user_id": user.id,
                "is_active": new_status,
                "reason": "admin_action"
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Обновление в user-db
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="update_user_profile",
            event_type="saga.step.update_user_profile",
            payload={
                "keycloak_id": keycloak_id,
                "update_data": {"is_active": new_status}
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 3: Публикация подтверждения изменения статуса
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_status_update",
            step_name="publish_user_updated",
            event_type="saga.step.publish_user_updated",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "updated_fields": {"is_active": new_status},
                "source_service": "user-service"
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "update_user_profile"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Status change initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "Status change initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/users/saga/{saga_id}/status"
        }

    # ========== ОБНОВЛЕНИЕ РОЛЕЙ ==========
    
    async def update_user_roles(
        self,
        keycloak_id: str,
        roles_data: UserRolesUpdate,
        current_user: dict
    ) -> Dict[str, Any]:
        """АСИНХРОННОЕ обновление ролей пользователя"""
        user = await self.get_user_by_keycloak_id(keycloak_id)
        
        if not user:
            raise UserNotFoundException(f"User with keycloak_id {keycloak_id} not found")
        
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        old_roles = [role.value for role in user.roles]
        new_roles = [role.value for role in roles_data.roles]
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Отправляем запрос в auth-service
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_roles_update",
            step_name="publish_user_roles_update_requested",
            event_type="saga.step.publish_user_roles_update_requested",
            payload={
                "keycloak_id": user.keycloak_id,
                "user_id": user.id,
                "roles": new_roles,
                "old_roles": old_roles
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Обновление ролей в user-db
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_roles_update",
            step_name="update_user_roles",
            event_type="saga.step.update_user_roles",
            payload={
                "keycloak_id": keycloak_id,
                "roles": new_roles,
                "old_roles": old_roles
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 3: Публикация подтверждения обновления ролей
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_roles_update",
            step_name="publish_user_roles_updated",
            event_type="saga.step.publish_user_roles_updated",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "roles": new_roles,
                "old_roles": old_roles,
                "source_service": "user-service"
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "update_user_roles"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Roles update initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "Roles update initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/users/saga/{saga_id}/status"
        }

    # ========== УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ==========
    
    async def delete_user(self, keycloak_id: str, current_user: dict) -> Dict[str, Any]:
        """АСИНХРОННОЕ удаление пользователя"""
        if UserRole.ADMIN not in current_user["roles"]:
            raise PermissionDeniedException("Not enough permissions")
        
        user = await self.get_user_by_keycloak_id(keycloak_id)
        
        if not user:
            raise UserNotFoundException(f"User with keycloak_id {keycloak_id} not found")
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Создаем все outbox записи
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="publish_user_deletion_requested",
            event_type="saga.step.publish_user_deletion_requested",
            payload={
                "keycloak_id": user.keycloak_id,
                "user_id": user.id
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="delete_user_profile",
            event_type="saga.step.delete_user_profile",
            payload={
                "keycloak_id": keycloak_id
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id
            }
        )
        
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="user_deletion",
            step_name="publish_user_deleted",
            event_type="saga.step.publish_user_deleted",
            payload={
                "keycloak_id": keycloak_id,
                "user_id": user.id,
                "source_service": "user-service"
            },
            headers={
                "source_service": "user-service",
                "correlation_id": saga_id,
                "depends_on": "delete_user_profile"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Deletion initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "User deletion initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/users/saga/{saga_id}/status"
        }

    # ========== СТАТУС САГИ ==========
    
    async def get_saga_status(self, saga_id: str) -> Dict[str, Any]:
        """Получение статуса саги"""
        status = await self.saga_worker.get_saga_status(saga_id)
        
        if not status:
            return {
                "status": "not_found",
                "saga_id": saga_id,
                "message": "Saga not found"
            }
        
        # Обогащаем данными пользователя если сага завершена
        if status["status"] == SagaStatus.COMPLETED:
            step_results = status.get("step_results", {})
            
            # Ищем созданного/обновлённого пользователя
            for step_name, result in step_results.items():
                if isinstance(result, dict) and result.get("keycloak_id"):
                    keycloak_id = result.get("keycloak_id")
                    user = await self.get_user_by_keycloak_id(keycloak_id)
                    if user:
                        status["user"] = {
                            "id": user.id,
                            "keycloak_id": user.keycloak_id,
                            "username": user.username,
                            "email": user.email,
                            "roles": [role.value for role in user.roles],
                            "is_active": user.is_active,
                            "is_test_passed": user.is_test_passed
                        }
                    break
        
        return status

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    async def update_user_from_event(
        self,
        keycloak_id: str,
        updated_fields: Dict[str, Any],
        source_service: str = "auth-service"
    ) -> bool:
        """Обновление пользователя из события (для обратной совместимости)"""
        user = await self.get_user_by_keycloak_id(keycloak_id)
        if not user:
            logger.warning(f"User {keycloak_id} not found in user-service")
            return False
        
        try:
            allowed_fields = ["email", "username", "is_active"]
            fields_to_update = {
                k: v for k, v in updated_fields.items() 
                if k in allowed_fields and v is not None
            }
            
            if not fields_to_update:
                logger.debug(f"No relevant fields to update for {keycloak_id}")
                return True
            
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
            
            for field, value in fields_to_update.items():
                if field in ['email', 'username']:
                    value = value.lower()
                setattr(user, field, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User {keycloak_id} updated from {source_service} confirmation")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {keycloak_id} from event: {e}")
            return False

    async def check_user_exists(self, keycloak_id: str) -> bool:
        try:
            user = await self.get_user_by_keycloak_id(keycloak_id)
            return user is not None
        except Exception:
            return False

    async def _get_user_by_id(self, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundException(f"User with id {user_id} not found")
        return user

    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_my_info(self, keycloak_id: str) -> Dict[str, Any]:
        user = await self.get_user_by_keycloak_id(keycloak_id)
        if not user:
            raise UserNotFoundException(f"User with keycloak_id {keycloak_id} not found")
        
        return {
            "id": user.id,
            "keycloak_id": user.keycloak_id,
            "username": user.username,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "is_active": user.is_active,
            "is_test_passed": user.is_test_passed,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    async def list_users(self, skip: int = 0, limit: int = 100) -> Tuple[List[User], int]:
        count_query = select(func.count()).select_from(User)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total

    async def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> Tuple[List[User], int]:
        count_query = (
            select(func.count())
            .select_from(User)
            .join(UserRoleAssignment)
            .where(UserRoleAssignment.role == role)
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        stmt = (
            select(User)
            .join(UserRoleAssignment)
            .where(UserRoleAssignment.role == role)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return users, total