import uuid
import asyncio
from typing import Dict, Any
from sqlalchemy import select

from shared.saga.orchestrator import SagaOrchestrator, SagaStep, get_saga_orchestrator
from shared.saga.compensation import CompensationRegistry, get_compensation_registry
from app.database.session import async_session_factory
from app.database.models import BasicProfile, DetailedProfile
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import DatabaseException, ProfileNotFoundException

class ProfileSagaService:
    def __init__(self):
        self.saga_orchestrator = get_saga_orchestrator()
        self.compensation_registry = get_compensation_registry()
        self._register_compensations()

    def _register_compensations(self):
        self.compensation_registry.register(
            name="delete_basic_profile",
            service="profile-service",
            action=self._compensate_basic_profile_creation,
            description="Delete basic profile as compensation"
        )
        self.compensation_registry.register(
            name="delete_detailed_profile",
            service="profile-service",
            action=self._compensate_detailed_profile_creation,
            description="Delete detailed profile as compensation"
        )

    async def _compensate_basic_profile_creation(self, context: Dict[str, Any]) -> bool:
        try:
            keycloak_id = context.get("keycloak_id")
            if not keycloak_id:
                logger.error("No keycloak_id in compensation context")
                return False
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                if profile:
                    await session.delete(profile)
                    await session.commit()
                    logger.info(f"Compensated: deleted basic profile {keycloak_id}")
                else:
                    logger.warning(f"Basic profile {keycloak_id} not found during compensation")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate basic profile creation: {e}")
            return False

    async def _compensate_detailed_profile_creation(self, context: Dict[str, Any]) -> bool:
        try:
            basic_profile_id = context.get("basic_profile_id")
            if not basic_profile_id:
                logger.error("No basic_profile_id in compensation context")
                return False
            async with async_session_factory() as session:
                stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic_profile_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                if profile:
                    await session.delete(profile)
                    await session.commit()
                    logger.info(f"Compensated: deleted detailed profile for {basic_profile_id}")
                else:
                    logger.warning(f"Detailed profile for {basic_profile_id} not found during compensation")
                return True
        except Exception as e:
            logger.error(f"Failed to compensate detailed profile creation: {e}")
            return False

    async def execute_profile_creation_saga(
        self,
        keycloak_id: str,
        basic_data: Dict[str, Any],
        detailed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        async def create_basic_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    # Проверяем существование
                    stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    if result.scalar_one_or_none():
                        raise DatabaseException("Basic profile already exists")
                    
                    profile = BasicProfile(
                        keycloak_id=keycloak_id,
                        **basic_data
                    )
                    session.add(profile)
                    await session.commit()
                    await session.refresh(profile)
                    
                    return {
                        "basic_profile_id": profile.id,
                        "saga_context": {"basic_profile_id": profile.id}
                    }
            except Exception as e:
                raise DatabaseException(f"Failed to create basic profile: {str(e)}")

        async def compensate_basic(context: Dict[str, Any]) -> bool:
            return await self._compensate_basic_profile_creation(context)

        async def create_detailed_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                basic_profile_id = context.get("basic_profile_id")
                if not basic_profile_id:
                    raise DatabaseException("No basic_profile_id provided")
                
                async with async_session_factory() as session:
                    profile = DetailedProfile(
                        basic_profile_id=basic_profile_id,
                        **detailed_data
                    )
                    session.add(profile)
                    await session.commit()
                    return {"detailed_profile_created": True}
            except Exception as e:
                raise DatabaseException(f"Failed to create detailed profile: {str(e)}")

        async def compensate_detailed(context: Dict[str, Any]) -> bool:
            return await self._compensate_detailed_profile_creation(context)

        steps = [
            SagaStep(
                name="create_basic_profile",
                service="profile-service",
                action=create_basic_profile,
                compensation=compensate_basic
            ),
            SagaStep(
                name="create_detailed_profile",
                service="profile-service",
                action=create_detailed_profile,
                compensation=compensate_detailed
            )
        ]

        initial_context = {"keycloak_id": keycloak_id}
        return await self.saga_orchestrator.start_saga(
            name="profile_creation",
            steps=steps,
            initial_context=initial_context
        )

    async def execute_profile_update_saga(
        self,
        keycloak_id: str,
        basic_update_data: Dict[str, Any],
        detailed_update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        async def update_basic_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    profile = result.scalar_one_or_none()
                    
                    if not profile:
                        raise ProfileNotFoundException(f"Basic profile {keycloak_id} not found")
                    
                    for field, value in basic_update_data.items():
                        if hasattr(profile, field):
                            setattr(profile, field, value)
                    
                    await session.commit()
                    return {"basic_profile_updated": True}
            except Exception as e:
                raise DatabaseException(f"Failed to update basic profile: {str(e)}")

        async def update_detailed_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                basic_profile_id = context.get("basic_profile_id")
                if not basic_profile_id:
                    # Получаем basic_profile_id если не передан
                    async with async_session_factory() as session:
                        stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                        result = await session.execute(stmt)
                        profile = result.scalar_one_or_none()
                        if not profile:
                            raise ProfileNotFoundException(f"Basic profile {keycloak_id} not found")
                        basic_profile_id = profile.id

                async with async_session_factory() as session:
                    stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic_profile_id)
                    result = await session.execute(stmt)
                    detailed = result.scalar_one_or_none()
                    
                    if not detailed:
                        raise ProfileNotFoundException(f"Detailed profile for {keycloak_id} not found")
                    
                    for field, value in detailed_update_data.items():
                        if hasattr(detailed, field):
                            setattr(detailed, field, value)
                    
                    await session.commit()
                    return {"detailed_profile_updated": True}
            except Exception as e:
                raise DatabaseException(f"Failed to update detailed profile: {str(e)}")

        steps = [
            SagaStep(
                name="update_basic_profile",
                service="profile-service",
                action=update_basic_profile
            ),
            SagaStep(
                name="update_detailed_profile",
                service="profile-service",
                action=update_detailed_profile
            )
        ]

        initial_context = {"keycloak_id": keycloak_id}
        return await self.saga_orchestrator.start_saga(
            name="profile_update",
            steps=steps,
            initial_context=initial_context
        )

    async def execute_profile_deletion_saga(
        self,
        keycloak_id: str
    ) -> Dict[str, Any]:
        async def delete_detailed_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    basic_profile = result.scalar_one_or_none()
                    
                    if not basic_profile:
                        return {"detailed_profile_deleted": True}  # Уже удален
                    
                    stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic_profile.id)
                    result = await session.execute(stmt)
                    detailed_profile = result.scalar_one_or_none()
                    
                    if detailed_profile:
                        await session.delete(detailed_profile)
                        await session.commit()
                    
                    return {"detailed_profile_deleted": True}
            except Exception as e:
                raise DatabaseException(f"Failed to delete detailed profile: {str(e)}")

        async def delete_basic_profile(context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with async_session_factory() as session:
                    stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                    result = await session.execute(stmt)
                    basic_profile = result.scalar_one_or_none()
                    
                    if basic_profile:
                        await session.delete(basic_profile)
                        await session.commit()
                    
                    return {"basic_profile_deleted": True}
            except Exception as e:
                raise DatabaseException(f"Failed to delete basic profile: {str(e)}")

        steps = [
            SagaStep(
                name="delete_detailed_profile",
                service="profile-service",
                action=delete_detailed_profile
            ),
            SagaStep(
                name="delete_basic_profile",
                service="profile-service",
                action=delete_basic_profile
            )
        ]

        initial_context = {"keycloak_id": keycloak_id}
        return await self.saga_orchestrator.start_saga(
            name="profile_deletion",
            steps=steps,
            initial_context=initial_context
        )

_profile_saga_service = None

def get_profile_saga_service() -> ProfileSagaService:
    global _profile_saga_service
    if _profile_saga_service is None:
        _profile_saga_service = ProfileSagaService()
    return _profile_saga_service