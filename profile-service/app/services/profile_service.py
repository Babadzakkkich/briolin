import uuid
from datetime import datetime
from sqlalchemy import select, func
from typing import Dict, Any, Optional, Tuple, List

from app.database.models import BasicProfile, DetailedProfile
from app.database.session import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.profile import (
    FullProfileCreate, FullProfileUpdate
)
from app.services.keycloak_client import KeycloakClient

from app.services.event_service import get_event_service
from app.services.saga_worker import get_saga_worker
from app.core.exceptions import (
    ProfileNotFoundException, 
    ProfileAlreadyExistsException,
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


class ProfileService:
    def __init__(self, db: AsyncSession, kc_client: KeycloakClient):
        self.db = db
        self.kc = kc_client
        self.event_service = get_event_service()
        self.saga_worker = get_saga_worker()

    # ========== СОЗДАНИЕ ПРОФИЛЯ ==========
    
    async def create_full_profile(
        self,
        keycloak_id: str,
        profile_data: FullProfileCreate,
        current_user: dict
    ) -> Dict[str, Any]:
        """АСИНХРОННОЕ создание полного профиля через SAGA"""
        
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionDeniedException("Cannot create profile for another user")
        
        # Проверяем существование профиля (используем self.db!)
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if existing:
            logger.info(f"Profile already exists for {keycloak_id}")
            full_profile = await self.get_full_profile_by_keycloak_id(keycloak_id)
            return {
                "status": "success",
                "profile": full_profile,
                "already_exists": True
            }
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Создание базового профиля
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_creation",
            step_name="create_basic_profile",
            event_type="saga.step.create_basic_profile",
            payload={
                "keycloak_id": keycloak_id,
                "basic_data": profile_data.basic.model_dump()
            },
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Создание детального профиля
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_creation",
            step_name="create_detailed_profile",
            event_type="saga.step.create_detailed_profile",
            payload={
                "detailed_data": profile_data.detailed.model_dump()
            },
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id,
                "depends_on": "create_basic_profile"
            }
        )
        
        # Шаг 3: Публикация события о создании профиля
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_creation",
            step_name="publish_profile_created",
            event_type="saga.step.publish_profile_created",
            payload={},
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id,
                "depends_on": "create_basic_profile"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Profile creation initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "Profile creation initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/profiles/saga/{saga_id}/status"
        }
    
    # ========== ОБНОВЛЕНИЕ ПРОФИЛЯ ==========
    
    async def update_full_profile(
        self,
        keycloak_id: str,
        profile_data: FullProfileUpdate,
        current_user: dict
    ) -> Dict[str, Any]:
        """АСИНХРОННОЕ обновление полного профиля через SAGA"""

        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionDeniedException("Cannot update profile for another user")

        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if not existing:
            raise ProfileNotFoundException("Profile not found")

        # Подготавливаем данные
        basic_update = profile_data.basic.model_dump(exclude_unset=True) if profile_data.basic else {}
        detailed_update = profile_data.detailed.model_dump(exclude_unset=True) if profile_data.detailed else {}

        if not basic_update and not detailed_update:
            raise ValidationException("No data to update")

        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Обновление базового профиля (если есть данные)
        if basic_update:
            await self.saga_worker.create_saga_outbox(
                saga_id=saga_id,
                saga_name="profile_update",
                step_name="update_basic_profile",
                event_type="saga.step.update_basic_profile",
                payload={
                    "keycloak_id": keycloak_id,
                    "update_data": basic_update
                },
                headers={
                    "source_service": "profile-service",
                    "correlation_id": saga_id
                }
            )
        
        # Шаг 2: Обновление детального профиля (если есть данные)
        if detailed_update:
            detailed_depends_on = "update_basic_profile" if basic_update else None
            
            await self.saga_worker.create_saga_outbox(
                saga_id=saga_id,
                saga_name="profile_update",
                step_name="update_detailed_profile",
                event_type="saga.step.update_detailed_profile",
                payload={
                    "keycloak_id": keycloak_id,
                    "update_data": detailed_update
                },
                headers={
                    "source_service": "profile-service",
                    "correlation_id": saga_id,
                    "depends_on": detailed_depends_on
                }
            )
        
        # Шаг 3: Публикация события об обновлении профиля
        dependencies = []
        if basic_update:
            dependencies.append("update_basic_profile")
        if detailed_update:
            dependencies.append("update_detailed_profile")
        
        filtered_dependencies = _filter_dependencies(dependencies)
        all_updated_fields = {**basic_update, **detailed_update}
        
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_update",
            step_name="publish_profile_updated",
            event_type="saga.step.publish_profile_updated",
            payload={
                "keycloak_id": keycloak_id,
                "updated_fields": all_updated_fields
            },
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id,
                "depends_on": filtered_dependencies
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Profile update initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "Profile update initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/profiles/saga/{saga_id}/status"
        }

    # ========== УДАЛЕНИЕ ПРОФИЛЯ ==========
    
    async def delete_full_profile(
        self,
        keycloak_id: str,
        current_user: dict
    ) -> Dict[str, Any]:
        """АСИНХРОННОЕ удаление полного профиля через SAGA"""
        
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id and "admin" not in current_user.get("roles", []):
            raise PermissionDeniedException("Not enough permissions")
        
        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if not existing:
            return {
                "status": "success",
                "message": "Profile already deleted",
                "already_deleted": True
            }
        
        # Генерируем ID саги
        saga_id = str(uuid.uuid4())
        
        # Шаг 1: Удаление профиля
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_deletion",
            step_name="delete_basic_profile",
            event_type="saga.step.delete_basic_profile",
            payload={
                "keycloak_id": keycloak_id
            },
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id
            }
        )
        
        # Шаг 2: Публикация события об удалении профиля
        await self.saga_worker.create_saga_outbox(
            saga_id=saga_id,
            saga_name="profile_deletion",
            step_name="publish_profile_deleted",
            event_type="saga.step.publish_profile_deleted",
            payload={
                "keycloak_id": keycloak_id
            },
            headers={
                "source_service": "profile-service",
                "correlation_id": saga_id,
                "depends_on": "delete_basic_profile"
            }
        )
        
        await self.db.commit()
        
        logger.info(f"Profile deletion initiated for {keycloak_id} with saga_id: {saga_id}")
        
        return {
            "status": "accepted",
            "message": "Profile deletion initiated",
            "saga_id": saga_id,
            "check_status_url": f"/api/v1/profiles/saga/{saga_id}/status"
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
        
        # Обогащаем данными профиля если сага завершена
        if status["status"] == SagaStatus.COMPLETED:
            step_results = status.get("step_results", {})
            
            # Ищем созданный/обновлённый профиль
            for step_name, result in step_results.items():
                if isinstance(result, dict) and result.get("keycloak_id"):
                    keycloak_id = result.get("keycloak_id")
                    try:
                        profile = await self.get_full_profile_by_keycloak_id(keycloak_id)
                        status["profile"] = profile
                    except ProfileNotFoundException:
                        pass
                    break
        
        return status

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (с использованием self.db) ==========

    async def _get_basic_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[BasicProfile]:
        """Получение базового профиля по keycloak_id (внутренний метод)"""
        stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_full_profile_by_keycloak_id(self, keycloak_id: str) -> Dict[str, Any]:
        """Получение полного профиля по keycloak_id"""
        stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        basic = result.scalar_one_or_none()
        
        if not basic:
            raise ProfileNotFoundException(f"Profile not found for keycloak_id {keycloak_id}")
        
        stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic.id)
        result = await self.db.execute(stmt)
        detailed = result.scalar_one_or_none()
        
        response_data = {
            "basic": {
                "id": basic.id,
                "keycloak_id": basic.keycloak_id,
                "first_name": basic.first_name,
                "last_name": basic.last_name,
                "gender": basic.gender.value if hasattr(basic.gender, 'value') else basic.gender,
                "date_of_birth": basic.date_of_birth.isoformat() if basic.date_of_birth else None,
                "city": basic.city,
                "online": basic.online,
                "created_at": basic.created_at.isoformat() if basic.created_at else None,
                "updated_at": basic.updated_at.isoformat() if basic.updated_at else None,
                "last_login_at": basic.last_login_at.isoformat() if basic.last_login_at else None
            }
        }
        
        if detailed:
            response_data["detailed"] = {
                "id": detailed.id,
                "about_me": detailed.about_me,
                "education": detailed.education,
                "hobbies": detailed.hobbies,
                "partner_preferences": detailed.partner_preferences
            }
        else:
            response_data["detailed"] = None
        
        return response_data

    async def delete_profiles_by_keycloak_id(self, keycloak_id: str) -> bool:
        try:
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"No profiles found for user {keycloak_id}")
                    return True
                
                await session.delete(profile)
                await session.commit()
                
                logger.info(f"Profiles deleted for user {keycloak_id} by event")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete profiles by keycloak_id: {e}")
            return False

    async def update_online_status(self, keycloak_id: str, online: bool) -> bool:
        try:
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"Profile not found for {keycloak_id}")
                    return False
                
                profile.online = online
                if online:
                    profile.last_login_at = datetime.utcnow()
                
                await session.commit()
                
                status_str = "ONLINE" if online else "OFFLINE"
                logger.info(f"Online status updated for {keycloak_id}: {status_str}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update online status: {e}")
            return False
        
    async def get_online_users(
        self, 
        skip: int = 0, 
        limit: int = 50
    ) -> Dict[str, Any]:
        try:
            async with async_session_factory() as session:
                count_stmt = select(func.count()).select_from(BasicProfile).where(BasicProfile.online == True)
                count_result = await session.execute(count_stmt)
                total = count_result.scalar_one()
                
                stmt = (
                    select(BasicProfile)
                    .where(BasicProfile.online == True)
                    .order_by(BasicProfile.last_login_at.desc())
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                profiles = result.scalars().all()
                
                users = []
                for profile in profiles:
                    users.append({
                        "keycloak_id": profile.keycloak_id,
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "avatar_url": None,  # Можно добавить позже
                        "online": profile.online,
                        "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
                    })
                
                return {
                    "users": users,
                    "total": total,
                    "page": skip // limit + 1 if limit > 0 else 1,
                    "size": limit
                }
                
        except Exception as e:
            logger.error(f"Failed to get online users: {e}")
            raise

    async def get_user_online_status(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    return None
                
                return {
                    "keycloak_id": profile.keycloak_id,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "online": profile.online,
                    "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get user online status: {e}")
            return None