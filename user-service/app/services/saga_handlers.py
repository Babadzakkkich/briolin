import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import or_, select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, UserRoleAssignment
from app.database.session import async_session_factory
from app.services.keycloak_client import KeycloakClient
from app.core.logger import logger
from shared.schemas.shared import UserRole
from app.services.event_service import get_event_service


class UserSagaHandlers:
    """Обработчики шагов SAGA для user-service"""
    
    def __init__(self):
        self.kc_client = KeycloakClient()
        self.event_service = get_event_service()
    
    async def _get_step_result(self, saga_id: str, step_name: str) -> Dict[str, Any]:
        """Вспомогательный метод для получения результата шага"""
        async with async_session_factory() as session:
            from shared.saga.models import SagaInstance
            stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if instance and instance.step_results:
                return instance.step_results.get(step_name, {})
            return {}
    
    # ========== ОСНОВНЫЕ ШАГИ ==========
    
    async def handle_create_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Создание пользователя в user-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        email = payload.get("email")
        username = payload.get("username")
        role = payload.get("role", UserRole.USER.value)
        
        logger.info(f"[SAGA {saga_id}] Creating user profile in user-db: {email}")
        
        async with async_session_factory() as session:
            # Проверяем, нет ли уже такого пользователя
            stmt = select(User).where(
                or_(
                    User.keycloak_id == keycloak_id,
                    User.email == email,
                    User.username == username
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                if existing.keycloak_id == keycloak_id:
                    logger.warning(f"[SAGA {saga_id}] User already exists with keycloak_id: {keycloak_id}")
                    return {
                        "status": "success",
                        "user_id": existing.id,
                        "keycloak_id": keycloak_id,
                        "already_exists": True
                    }
                else:
                    error_msg = f"User with email {email} or username {username} already exists"
                    logger.error(f"[SAGA {saga_id}] {error_msg}")
                    raise Exception(error_msg)
            
            # Создаем нового пользователя
            new_user = User(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                is_active=True,
                is_test_passed=False
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            logger.info(f"[SAGA {saga_id}] User created in user-db: {new_user.id}")
            
            return {
                "status": "success",
                "user_id": new_user.id,
                "keycloak_id": keycloak_id,
                "email": email,
                "username": username
            }
    
    async def handle_assign_user_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Назначение роли пользователю"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        role = payload.get("role", UserRole.USER.value)
        
        # Получаем user_id из контекста
        create_step_result = context.get("create_user_profile", {})
        user_id = create_step_result.get("user_id")
        keycloak_id = create_step_result.get("keycloak_id")
        
        if not user_id:
            step_result = await self._get_step_result(saga_id, "create_user_profile")
            user_id = step_result.get("user_id")
            keycloak_id = step_result.get("keycloak_id")
        
        if not user_id:
            error_msg = f"[SAGA {saga_id}] Cannot assign role: missing user_id from previous step"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] Assigning role {role} to user {user_id}")
        
        async with async_session_factory() as session:
            # Проверяем, не назначена ли уже роль
            stmt = select(UserRoleAssignment).where(
                and_(
                    UserRoleAssignment.user_id == user_id,
                    UserRoleAssignment.role == role
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"[SAGA {saga_id}] Role {role} already assigned to user {user_id}")
                return {
                    "status": "success",
                    "user_id": user_id,
                    "role": role,
                    "already_assigned": True
                }
            
            # Назначаем роль
            role_assignment = UserRoleAssignment(
                user_id=user_id,
                role=UserRole(role)
            )
            session.add(role_assignment)
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Role {role} assigned to user {user_id}")
            
            return {
                "status": "success",
                "user_id": user_id,
                "role": role
            }
    
    async def handle_update_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление профиля пользователя в user-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        update_data = payload.get("update_data", {})
        
        logger.info(f"[SAGA {saga_id}] Updating user profile in user-db: {keycloak_id}")
        
        if not update_data:
            logger.warning(f"[SAGA {saga_id}] Empty update data for {keycloak_id}")
            return {"status": "success", "updated": False, "reason": "no_data"}
        
        async with async_session_factory() as session:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                error_msg = f"User {keycloak_id} not found in user-db"
                logger.error(f"[SAGA {saga_id}] {error_msg}")
                raise Exception(error_msg)
            
            # Обновляем поля
            updated_fields = []
            if 'email' in update_data:
                user.email = update_data['email'].lower()
                updated_fields.append('email')
            if 'username' in update_data:
                user.username = update_data['username'].lower()
                updated_fields.append('username')
            if 'is_active' in update_data:
                user.is_active = update_data['is_active']
                updated_fields.append('is_active')
            if 'is_test_passed' in update_data:
                user.is_test_passed = update_data['is_test_passed']
                updated_fields.append('is_test_passed')
            
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] User updated in user-db: {updated_fields}")
            
            return {
                "status": "success",
                "user_id": user.id,
                "keycloak_id": keycloak_id,
                "updated_fields": updated_fields
            }
    
    async def handle_update_user_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление ролей пользователя в user-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        new_roles = payload.get("roles", [])
        
        logger.info(f"[SAGA {saga_id}] Updating roles for user {keycloak_id}: {new_roles}")
        
        async with async_session_factory() as session:
            # Находим пользователя
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                error_msg = f"User {keycloak_id} not found in user-db"
                logger.error(f"[SAGA {saga_id}] {error_msg}")
                raise Exception(error_msg)
            
            # Удаляем старые роли
            await session.execute(
                delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user.id)
            )
            
            # Добавляем новые роли
            for role in new_roles:
                role_assignment = UserRoleAssignment(
                    user_id=user.id,
                    role=UserRole(role)
                )
                session.add(role_assignment)
            
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Roles updated for user {keycloak_id}: {new_roles}")
            
            return {
                "status": "success",
                "user_id": user.id,
                "keycloak_id": keycloak_id,
                "roles": new_roles
            }
    
    async def handle_delete_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Удаление пользователя из user-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        
        logger.info(f"[SAGA {saga_id}] Deleting user profile from user-db: {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"[SAGA {saga_id}] User {keycloak_id} not found in user-db")
                return {"status": "success", "deleted": False, "reason": "not_found"}
            
            await session.delete(user)
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] User deleted from user-db: {keycloak_id}")
            
            return {
                "status": "success",
                "keycloak_id": keycloak_id,
                "deleted": True
            }
    
    # ========== ШАГИ ПУБЛИКАЦИИ СОБЫТИЙ (ЗАПРОСЫ К AUTH-SERVICE) ==========
    
    async def handle_publish_user_profile_update_requested(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация запроса обновления профиля в auth-service"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_PROFILE_UPDATE_REQUESTED to auth-service")
        
        success = await self.event_service.publish_user_profile_update_requested(
            keycloak_id=payload["keycloak_id"],
            user_id=payload["user_id"],
            updated_fields=payload["updated_fields"],
            old_values=payload.get("old_values", {}),
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_PROFILE_UPDATE_REQUESTED"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_PROFILE_UPDATE_REQUESTED published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_status_change_requested(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация запроса изменения статуса в auth-service"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_STATUS_CHANGE_REQUESTED to auth-service")
        
        success = await self.event_service.publish_user_status_change_requested(
            keycloak_id=payload["keycloak_id"],
            user_id=payload["user_id"],
            is_active=payload["is_active"],
            reason=payload.get("reason"),
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_STATUS_CHANGE_REQUESTED"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_STATUS_CHANGE_REQUESTED published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_roles_update_requested(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация запроса обновления ролей в auth-service"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_ROLES_UPDATE_REQUESTED to auth-service")
        
        success = await self.event_service.publish_user_roles_update_requested(
            keycloak_id=payload["keycloak_id"],
            user_id=payload["user_id"],
            roles=payload["roles"],
            old_roles=payload.get("old_roles", []),
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_ROLES_UPDATE_REQUESTED"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_ROLES_UPDATE_REQUESTED published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_deletion_requested(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация запроса удаления пользователя в auth-service"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_DELETION_REQUESTED to auth-service")
        
        success = await self.event_service.publish_user_deletion_requested(
            keycloak_id=payload["keycloak_id"],
            user_id=payload.get("user_id"),
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_DELETION_REQUESTED"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_DELETION_REQUESTED published")
        return {"status": "success", "event_published": True}
    
    # ========== ШАГИ ПУБЛИКАЦИИ ПОДТВЕРЖДЕНИЙ ==========
    
    async def handle_publish_user_profile_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_PROFILE_CREATED"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_PROFILE_CREATED event")
        
        # Получаем данные из контекста
        create_step = context.get("create_user_profile", {})
        user_id = create_step.get("user_id")
        keycloak_id = create_step.get("keycloak_id")
        email = create_step.get("email")
        username = create_step.get("username")
        
        if not user_id or not keycloak_id:
            # Пробуем из результатов шага
            step_result = await self._get_step_result(saga_id, "create_user_profile")
            user_id = step_result.get("user_id")
            keycloak_id = step_result.get("keycloak_id")
            email = step_result.get("email")
            username = step_result.get("username")
        
        if not user_id or not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing user data for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Получаем роли пользователя
        roles = [payload.get("role", UserRole.USER.value)]
        
        success = await self.event_service.publish_user_profile_created(
            keycloak_id=keycloak_id,
            user_id=user_id,
            username=username,
            email=email,
            roles=roles,
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_PROFILE_CREATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_PROFILE_CREATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_PROFILE_UPDATED (подтверждение обновления)"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_PROFILE_UPDATED confirmation")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        updated_fields = payload.get("updated_fields", {})
        source_service = payload.get("source_service", "user-service")
        
        if not keycloak_id or not user_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id or user_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        success = await self.event_service.publish_user_profile_updated(
            keycloak_id=keycloak_id,
            user_id=user_id,
            updated_fields=updated_fields,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_PROFILE_UPDATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_PROFILE_UPDATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_roles_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_ROLES_UPDATED (подтверждение обновления ролей)"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_ROLES_UPDATED confirmation")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        roles = payload.get("roles", [])
        old_roles = payload.get("old_roles", [])
        source_service = payload.get("source_service", "user-service")
        
        if not keycloak_id or not user_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id or user_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        success = await self.event_service.publish_user_roles_updated(
            keycloak_id=keycloak_id,
            user_id=user_id,
            roles=roles,
            old_roles=old_roles,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_ROLES_UPDATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_ROLES_UPDATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_user_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация USER_DELETED (подтверждение удаления)"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing USER_DELETED confirmation")
        
        keycloak_id = payload.get("keycloak_id")
        user_id = payload.get("user_id")
        source_service = payload.get("source_service", "user-service")
        
        if not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        success = await self.event_service.publish_user_deleted(
            keycloak_id=keycloak_id,
            user_id=user_id,
            correlation_id=saga_id,
            source_service=source_service
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish USER_DELETED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] USER_DELETED event published")
        return {"status": "success", "event_published": True}
    
    # ========== КОМПЕНСАЦИИ ==========
    
    async def handle_compensate_create_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Компенсация: удаление пользователя из user-db"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        create_step_result = context.get("create_user_profile", {})
        keycloak_id = create_step_result.get("keycloak_id")
        
        if not keycloak_id:
            keycloak_id = payload.get("keycloak_id")
        
        if not keycloak_id:
            logger.warning(f"[SAGA {saga_id}] No keycloak_id for compensation")
            return {"status": "success", "reason": "no_keycloak_id"}
        
        logger.info(f"[SAGA {saga_id}] Compensating: deleting user from user-db: {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = select(User).where(User.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                await session.delete(user)
                await session.commit()
                logger.info(f"[SAGA {saga_id}] User deleted from user-db during compensation")
                return {"status": "success", "deleted": True}
            else:
                logger.warning(f"[SAGA {saga_id}] User not found in user-db during compensation")
                return {"status": "success", "deleted": False}
    
    async def handle_compensate_assign_user_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Компенсация: удаление роли пользователя"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        create_step_result = context.get("create_user_profile", {})
        user_id = create_step_result.get("user_id")
        
        if not user_id:
            logger.warning(f"[SAGA {saga_id}] No user_id for role compensation")
            return {"status": "success", "reason": "no_user_id"}
        
        logger.info(f"[SAGA {saga_id}] Compensating: removing roles for user {user_id}")
        
        async with async_session_factory() as session:
            await session.execute(
                delete(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            )
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Roles removed for user {user_id}")
            return {"status": "success", "user_id": user_id}