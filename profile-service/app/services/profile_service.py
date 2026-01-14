import asyncio
from datetime import datetime
from sqlalchemy import select, func
from typing import Dict, Any, Optional, Tuple

from app.database.models import BasicProfile, DetailedProfile
from app.database.session import async_session_factory
from app.schemas.profile import (
    FullProfileCreate, FullProfileUpdate
)
from app.services.keycloak_client import KeycloakClient
from app.services.event_service import get_event_service
from app.services.saga_service import get_profile_saga_service
from app.core.exceptions import (
    ProfileNotFoundException, 
    ProfileAlreadyExistsException,
    DatabaseException,
    ValidationException
)
from app.core.logger import logger

class ProfileService:
    def __init__(self, kc_client: KeycloakClient):
        self.kc = kc_client
        self.event_service = get_event_service()
        self.saga_service = get_profile_saga_service()

    async def create_full_profile(
        self,
        keycloak_id: str,
        profile_data: FullProfileCreate,
        current_user: dict
    ) -> Dict[str, Any]:
        """Создание полного профиля (basic + detailed) через SAGA"""
        
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionError("Cannot create profile for another user")
        
        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if existing:
            raise ProfileAlreadyExistsException("Profile already exists for this user")
        
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_profile_creation_saga(
            keycloak_id=keycloak_id,
            basic_data=profile_data.basic.model_dump(),
            detailed_data=profile_data.detailed.model_dump()
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        final_status = await self._wait_for_saga_completion(saga_id)
        
        if final_status["status"] == "completed":
            # Получаем полный профиль из БД
            full_profile = await self._get_full_profile_by_keycloak_id(keycloak_id)
            
            # Обновляем имя в Keycloak через событие
            try:
                await self.event_service.publish_keycloak_update_requested(
                    keycloak_id=keycloak_id,
                    first_name=profile_data.basic.first_name,
                    last_name=profile_data.basic.last_name
                )
            except Exception as e:
                logger.warning(f"Failed to update Keycloak name: {e}")
            
            logger.info(f"Full profile created via SAGA")
            return full_profile
            
        elif final_status["status"] == "compensated":
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"Profile creation failed and was compensated: {error_msg}")
        else:
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"Profile creation failed: {error_msg}")

    async def _wait_for_saga_completion(self, saga_id: str) -> Dict[str, Any]:
        """Ожидание завершения SAGA в отдельной асинхронной функции"""
        for _ in range(30):
            await asyncio.sleep(1)
            status = await self.saga_service.saga_orchestrator.get_saga_status(saga_id)
            
            if status and status["status"] in ["completed", "compensated", "failed"]:
                return status
        
        return {"status": "timeout", "error": "SAGA timeout"}

    async def _get_basic_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[BasicProfile]:
        """Получение базового профиля с новой сессией"""
        async with async_session_factory() as session:
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def _get_full_profile_by_keycloak_id(self, keycloak_id: str) -> Dict[str, Any]:
        """Получение полного профиля с новой сессией"""
        async with async_session_factory() as session:
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            basic = result.scalar_one_or_none()
            
            if not basic:
                raise ProfileNotFoundException(f"Profile not found for keycloak_id {keycloak_id}")
            
            # Явно загружаем detailed profile
            stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic.id)
            result = await session.execute(stmt)
            detailed = result.scalar_one_or_none()
            
            response_data = {
                "basic": {
                    "id": basic.id,
                    "keycloak_id": basic.keycloak_id,
                    "first_name": basic.first_name,
                    "last_name": basic.last_name,
                    "gender": basic.gender,
                    "date_of_birth": basic.date_of_birth,
                    "city": basic.city,
                    "online": basic.online,
                    "created_at": basic.created_at,
                    "updated_at": basic.updated_at,
                    "last_login_at": basic.last_login_at
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

    async def update_full_profile(
        self,
        keycloak_id: str,
        profile_data: FullProfileUpdate,
        current_user: dict
    ) -> Dict[str, Any]:
        """Обновление полного профиля через SAGA"""
        
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionError("Cannot update profile for another user")
        
        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if not existing:
            raise ProfileNotFoundException("Profile not found")
        
        # Подготавливаем данные
        basic_update = profile_data.basic.model_dump(exclude_unset=True) if profile_data.basic else {}
        detailed_update = profile_data.detailed.model_dump(exclude_unset=True) if profile_data.detailed else {}
        
        if not basic_update and not detailed_update:
            raise ValidationException("No data to update")
        
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_profile_update_saga(
            keycloak_id=keycloak_id,
            basic_update_data=basic_update,
            detailed_update_data=detailed_update
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        final_status = await self._wait_for_saga_completion(saga_id)
        
        if final_status["status"] == "completed":
            # Обновляем имя в Keycloak если нужно
            if basic_update and ("first_name" in basic_update or "last_name" in basic_update):
                try:
                    await self.event_service.publish_keycloak_update_requested(
                        keycloak_id=keycloak_id,
                        first_name=basic_update.get("first_name"),
                        last_name=basic_update.get("last_name")
                    )
                except Exception as e:
                    logger.warning(f"Failed to update Keycloak name: {e}")
            
            logger.info(f"Full profile updated via SAGA: {keycloak_id}")
            return await self._get_full_profile_by_keycloak_id(keycloak_id)
            
        else:
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"Profile update failed: {error_msg}")

    async def delete_full_profile(
        self,
        keycloak_id: str,
        current_user: dict
    ) -> bool:
        """Удаление полного профиля через SAGA"""
        
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id and "admin" not in current_user["roles"]:
            raise PermissionError("Not enough permissions")
        
        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if not existing:
            return True  # Уже удален
        
        # Запускаем SAGA транзакцию
        saga_result = await self.saga_service.execute_profile_deletion_saga(
            keycloak_id=keycloak_id
        )
        
        saga_id = saga_result["saga_id"]
        
        # Ждем завершения SAGA
        final_status = await self._wait_for_saga_completion(saga_id)
        
        if final_status["status"] == "completed":
            logger.info(f"Full profile deleted via SAGA: {keycloak_id}")
            return True
        else:
            error_msg = final_status.get("error", "Unknown error")
            raise DatabaseException(f"Profile deletion failed: {error_msg}")

    async def delete_profiles_by_keycloak_id(self, keycloak_id: str) -> bool:
        """Удаление профилей по событию из auth-service (внутренний метод)"""
        try:
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"No profiles found for user {keycloak_id}")
                    return True
                
                # Удаляем каскадно (detailed удалится автоматически)
                await session.delete(profile)
                await session.commit()
                
                logger.info(f"Profiles deleted for user {keycloak_id} by event")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete profiles by keycloak_id: {e}")
            return False

    async def update_online_status(self, keycloak_id: str, online: bool) -> bool:
        """Обновление онлайн статуса пользователя"""
        try:
            async with async_session_factory() as session:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    return False
                
                profile.online = online
                if online:
                    profile.last_login_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Online status updated for {keycloak_id}: {online}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update online status: {e}")
            return False