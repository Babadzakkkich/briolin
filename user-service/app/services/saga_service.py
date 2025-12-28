import uuid
import asyncio
from typing import Dict, Any
from sqlalchemy import select, delete

from shared.saga.orchestrator import SagaOrchestrator, SagaStep, get_saga_orchestrator
from shared.saga.compensation import CompensationRegistry, get_compensation_registry
from app.database.session import async_session_factory
from app.database.models import User, UserRoleAssignment
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import DatabaseException, UserNotFoundException

class UserSagaService:
    def __init__(self):
        self.saga_orchestrator = get_saga_orchestrator()
        self.compensation_registry = get_compensation_registry()
        self._register_compensations()

    def _register_compensations(self):
        self.compensation_registry.register(
            name="delete_user_profile",
            service="user-service",
            action=self._compensate_user_profile_creation,
            description="Delete user profile as compensation"
        )
        self.compensation_registry.register(
            name="rollback_user_profile_update",
            service="user-service",
            action=self._compensate_user_profile_update,
            description="Rollback user profile update"
        )

    async def _compensate_user_profile_creation(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            if not keycloak_id:
                logger.error("No keycloak_id in compensation context")
                return False
            async with async_session_factory() as session:
                stmt = select(User).where(User.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    await session.delete(user)
                    await session.commit()
                    logger.info(f"Compensated: deleted user profile {keycloak_id}")
                else:
                    logger.warning(f"User profile {keycloak_id} not found during compensation")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate user profile creation: {e}")
            return False

    async def _compensate_user_profile_update(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            old_values = context.get("old_values", {})
            if not keycloak_id or not old_values:
                logger.error("Missing keycloak_id or old_values in compensation context")
                return False
            async with async_session_factory() as session:
                stmt = select(User).where(User.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if not user:
                    logger.warning(f"User {keycloak_id} not found during compensation")
                    return False
                for field, value in old_values.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                await session.commit()
                logger.info(f"Compensated: rolled back user profile update for {keycloak_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate user profile update: {e}")
            return False

    async def execute_profile_creation_saga(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        role: str
    ) -> Dict[str, Any]:
        async def create_in_user_db(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(User).where((User.email == email) | (User.username == username))
                    result = await session.execute(stmt)
                    if result.scalar_one_or_none():
                        raise DatabaseException("Email or username already exists")
                    new_user = User(
                        keycloak_id=keycloak_id,
                        username=username,
                        email=email,
                    )
                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    return {
                        "user_id": new_user.id,
                        "saga_context": {"user_id": new_user.id}
                    }
            except Exception as e:
                raise DatabaseException(f"Failed to create user in user-db: {str(e)}")

        async def compensate_user_db(context: Dict[str, Any]) -> bool:
            return await self._compensate_user_profile_creation(context)

        async def assign_role(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                user_id = context.get("user_id")
                async with async_session_factory() as session:
                    role_assignment = UserRoleAssignment(
                        user_id=user_id,
                        role=role
                    )
                    session.add(role_assignment)
                    await session.commit()
                    return {"role_assigned": True}
            except Exception as e:
                raise DatabaseException(f"Failed to assign role: {str(e)}")

        steps = [
            SagaStep(
                name="create_user_profile",
                service="user-service",
                action=create_in_user_db,
                compensation=compensate_user_db
            ),
            SagaStep(
                name="assign_user_role",
                service="user-service",
                action=assign_role
            )
        ]

        initial_context = {
            "keycloak_id": keycloak_id,
            "email": email,
            "username": username,
            "role": role
        }

        return await self.saga_orchestrator.start_saga(
            name="user_profile_creation",
            steps=steps,
            initial_context=initial_context
        )

    async def execute_profile_update_saga(
        self,
        user_id: int,
        update_data: Dict[str, Any],
        old_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        async def update_in_user_db(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(User).where(User.id == user_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if not user:
                        raise DatabaseException(f"User {user_id} not found")
                    for field, value in update_data.items():
                        if hasattr(user, field):
                            setattr(user, field, value)
                    await session.commit()
                    return {"updated": True}
            except Exception as e:
                raise DatabaseException(f"Failed to update user in user-db: {str(e)}")

        async def compensate_user_db_update(context: Dict[str, Any]) -> bool:
            return await self._compensate_user_profile_update(context)

        steps = [
            SagaStep(
                name="update_user_profile",
                service="user-service",
                action=update_in_user_db,
                compensation=compensate_user_db_update
            )
        ]

        initial_context = {
            "user_id": user_id,
            "update_data": update_data,
            "old_values": old_values
        }

        return await self.saga_orchestrator.start_saga(
            name="user_profile_update",
            steps=steps,
            initial_context=initial_context
        )

_user_saga_service = None

def get_user_saga_service() -> UserSagaService:
    global _user_saga_service
    if _user_saga_service is None:
        _user_saga_service = UserSagaService()
    return _user_saga_service