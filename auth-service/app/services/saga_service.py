import uuid
import asyncio
from typing import Dict, Any
from sqlalchemy import select

from shared.saga.orchestrator import SagaOrchestrator, SagaStep, get_saga_orchestrator
from shared.saga.compensation import CompensationRegistry, get_compensation_registry
from app.services.keycloak_client import KeycloakClient
from app.database.session import async_session_factory
from app.database.models import User
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import DatabaseException, KeycloakConnectionError, UserAlreadyExistsException

class AuthSagaService:
    def __init__(self):
        self.saga_orchestrator = get_saga_orchestrator()
        self.compensation_registry = get_compensation_registry()
        self._register_compensations()

    def _register_compensations(self):
        self.compensation_registry.register(
            name="delete_user_from_keycloak",
            service="auth-service",
            action=self._compensate_keycloak_user_creation,
            description="Delete user from Keycloak as compensation"
        )
        self.compensation_registry.register(
            name="delete_user_from_auth_db",
            service="auth-service",
            action=self._compensate_auth_db_user_creation,
            description="Delete user from auth database as compensation"
        )
        self.compensation_registry.register(
            name="rollback_keycloak_status_update",
            service="auth-service",
            action=self._compensate_keycloak_status_update,
            description="Rollback user status update in Keycloak"
        )
        self.compensation_registry.register(
            name="rollback_auth_db_status_update",
            service="auth-service",
            action=self._compensate_auth_db_status_update,
            description="Rollback user status update in auth-db"
        )

    async def _compensate_keycloak_user_creation(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            if not keycloak_id:
                logger.error("No keycloak_id in compensation context")
                return False
            kc_client = KeycloakClient()
            success = kc_client.delete_user_from_keycloak(keycloak_id)
            if success:
                logger.info(f"Compensated: deleted user {keycloak_id} from Keycloak")
            else:
                logger.warning(f"Failed to delete user {keycloak_id} from Keycloak during compensation")
            return success
        except Exception as e:
            logger.error(f"Failed to compensate Keycloak user creation: {e}")
            return False

    async def _compensate_auth_db_user_creation(self, context: Dict[str, Any]) -> bool:
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
                    logger.info(f"Compensated: deleted user {keycloak_id} from auth-db")
                else:
                    logger.warning(f"User {keycloak_id} not found in auth-db during compensation")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate auth-db user creation: {e}")
            return False

    async def _compensate_keycloak_status_update(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            old_is_active = context.get("old_is_active")
            if not keycloak_id or old_is_active is None:
                logger.error("Missing keycloak_id or old_is_active in compensation context")
                return False
            kc_client = KeycloakClient()
            kc_client.update_user_status_in_keycloak(keycloak_id, old_is_active)
            logger.info(f"Compensated: rolled back Keycloak status for user {keycloak_id} to {old_is_active}")
            return True
        except Exception as e:
            logger.error(f"Failed to compensate Keycloak status update: {e}")
            return False

    async def _compensate_auth_db_status_update(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            old_is_active = context.get("old_is_active")
            if not keycloak_id or old_is_active is None:
                logger.error("Missing keycloak_id or old_is_active in compensation context")
                return False
            async with async_session_factory() as session:
                stmt = select(User).where(User.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if not user:
                    logger.warning(f"User {keycloak_id} not found during status compensation")
                    return False
                user.is_active = old_is_active
                await session.commit()
                logger.info(f"Compensated: rolled back auth-db status for user {keycloak_id} to {old_is_active}")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate auth-db status update: {e}")
            return False

    async def execute_user_registration_saga(
        self,
        email: str,
        username: str,
        password: str,
        role: str
    ) -> Dict[str, Any]:
        kc_client = KeycloakClient()

        existing_user_by_email = kc_client.get_user_by_email(email)
        if existing_user_by_email:
            raise UserAlreadyExistsException(f"User with email {email} already exists in Keycloak")
        existing_user_by_username = kc_client.get_user_by_username(username)
        if existing_user_by_username:
            raise UserAlreadyExistsException(f"User with username {username} already exists in Keycloak")

        async with async_session_factory() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise UserAlreadyExistsException(f"User with email {email} already exists in auth-db")

        async def create_in_keycloak(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                kc_client = KeycloakClient()
                keycloak_id, _ = kc_client.create_user_with_compensation(
                    email=email,
                    username=username,
                    password=password,
                    role=role
                )
                return {
                    "keycloak_id": keycloak_id,
                    "saga_context": {"keycloak_id": keycloak_id}
                }
            except UserAlreadyExistsException:
                raise
            except Exception as e:
                raise DatabaseException(f"Failed to create user in Keycloak: {str(e)}")

        async def compensate_keycloak(context: Dict[str, Any]) -> bool:
            return await self._compensate_keycloak_user_creation(context)

        async def create_in_auth_db(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                keycloak_id = context.get("keycloak_id")
                if not keycloak_id:
                    raise DatabaseException("No keycloak_id provided for auth-db creation")
                async with async_session_factory() as session:
                    new_user = User(
                        keycloak_id=keycloak_id,
                        email=email,
                        is_active=True
                    )
                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    return {
                        "user_id": new_user.id,
                        "saga_context": {"user_id": new_user.id}
                    }
            except Exception as e:
                raise DatabaseException(f"Failed to create user in auth-db: {str(e)}")

        async def compensate_auth_db(context: Dict[str, Any]) -> bool:
            return await self._compensate_auth_db_user_creation(context)

        steps = [
            SagaStep(
                name="create_keycloak_user",
                service="auth-service",
                action=create_in_keycloak,
                compensation=compensate_keycloak
            ),
            SagaStep(
                name="create_auth_db_user",
                service="auth-service",
                action=create_in_auth_db,
                compensation=compensate_auth_db
            )
        ]

        initial_context = {
            "email": email,
            "username": username,
            "role": role
        }

        return await self.saga_orchestrator.start_saga(
            name="user_registration",
            steps=steps,
            initial_context=initial_context
        )

    async def execute_user_status_update_saga(
        self,
        keycloak_id: str,
        is_active: bool,
        old_is_active: bool
    ) -> Dict[str, Any]:
        async def update_status_in_keycloak(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                kc_client = KeycloakClient()
                kc_client.update_user_status_in_keycloak(keycloak_id, is_active)
                return {"updated": True}
            except Exception as e:
                raise KeycloakConnectionError(f"Failed to update user status in Keycloak: {str(e)}")

        async def compensate_keycloak_status(context: Dict[str, Any]) -> bool:
            return await self._compensate_keycloak_status_update({
                "keycloak_id": keycloak_id,
                "old_is_active": old_is_active
            })

        async def update_status_in_auth_db(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(User).where(User.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if not user:
                        raise DatabaseException(f"User {keycloak_id} not found in auth-db")
                    user.is_active = is_active
                    await session.commit()
                    return {"updated": True}
            except Exception as e:
                raise DatabaseException(f"Failed to update user status in auth-db: {str(e)}")

        async def compensate_auth_db_status(context: Dict[str, Any]) -> bool:
            return await self._compensate_auth_db_status_update({
                "keycloak_id": keycloak_id,
                "old_is_active": old_is_active
            })

        steps = [
            SagaStep(
                name="update_keycloak_status",
                service="auth-service",
                action=update_status_in_keycloak,
                compensation=compensate_keycloak_status
            ),
            SagaStep(
                name="update_auth_db_status",
                service="auth-service",
                action=update_status_in_auth_db,
                compensation=compensate_auth_db_status
            )
        ]

        initial_context = {
            "keycloak_id": keycloak_id,
            "is_active": is_active,
            "old_is_active": old_is_active
        }

        return await self.saga_orchestrator.start_saga(
            name="user_status_update",
            steps=steps,
            initial_context=initial_context
        )

    async def execute_user_profile_update_saga(
        self,
        keycloak_id: str,
        update_data: Dict[str, Any],
        old_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        async def update_in_keycloak(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                kc_client = KeycloakClient()
                kc_client.update_user_in_keycloak(keycloak_id, update_data)
                return {"updated": True}
            except Exception as e:
                raise KeycloakConnectionError(f"Failed to update user in Keycloak: {str(e)}")

        async def compensate_keycloak_update(context: Dict[str, Any]) -> bool:
            logger.warning(f"Cannot fully compensate Keycloak update for {keycloak_id}, partial rollback attempted")
            try:
                kc_client = KeycloakClient()
                if old_values:
                    kc_client.update_user_in_keycloak(keycloak_id, old_values)
                    logger.info(f"Partially compensated Keycloak update for {keycloak_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to partially compensate Keycloak update: {e}")
                return False

        async def update_in_auth_db(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(User).where(User.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if not user:
                        raise DatabaseException(f"User {keycloak_id} not found in auth-db")
                    if "email" in update_data:
                        user.email = update_data["email"]
                    if "is_active" in update_data:
                        user.is_active = update_data["is_active"]
                    await session.commit()
                    return {"updated": True}
            except Exception as e:
                raise DatabaseException(f"Failed to update user in auth-db: {str(e)}")

        steps = [
            SagaStep(
                name="update_keycloak_user",
                service="auth-service",
                action=update_in_keycloak,
                compensation=compensate_keycloak_update
            ),
            SagaStep(
                name="update_auth_db_user",
                service="auth-service",
                action=update_in_auth_db
            )
        ]

        initial_context = {
            "keycloak_id": keycloak_id,
            "update_data": update_data,
            "old_values": old_values
        }

        return await self.saga_orchestrator.start_saga(
            name="user_profile_update",
            steps=steps,
            initial_context=initial_context
        )

_auth_saga_service = None

def get_auth_saga_service() -> AuthSagaService:
    global _auth_saga_service
    if _auth_saga_service is None:
        _auth_saga_service = AuthSagaService()
    return _auth_saga_service