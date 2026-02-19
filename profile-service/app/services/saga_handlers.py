import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BasicProfile, DetailedProfile
from app.database.session import async_session_factory
from app.services.keycloak_client import KeycloakClient
from app.core.logger import logger
from shared.schemas.shared import Gender

def serialize_for_json(obj):
    """Сериализатор для объектов, которые не могут быть напрямую преобразованы в JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, 'value'):  # для Enum
        return obj.value
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class ProfileSagaHandlers:
    """Обработчики шагов SAGA для profile-service"""
    
    def __init__(self):
        self.kc_client = KeycloakClient()
    
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
    
    async def handle_create_basic_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Создание базового профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        basic_data = payload.get("basic_data", {})
        
        logger.info(f"[SAGA {saga_id}] Creating basic profile for user: {keycloak_id}")
        
        async with async_session_factory() as session:
            # Проверяем, нет ли уже профиля
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"[SAGA {saga_id}] Basic profile already exists for {keycloak_id}")
                return {
                    "status": "success",
                    "basic_profile_id": existing.id,
                    "keycloak_id": keycloak_id,
                    "already_exists": True
                }
            
            # Обрабатываем date_of_birth - преобразуем строку в date
            date_of_birth = None
            if "date_of_birth" in basic_data:
                if isinstance(basic_data["date_of_birth"], str):
                    date_of_birth = datetime.fromisoformat(basic_data["date_of_birth"]).date()
                else:
                    date_of_birth = basic_data["date_of_birth"]
            
            # Создаем базовый профиль
            new_profile = BasicProfile(
                keycloak_id=keycloak_id,
                first_name=basic_data.get("first_name", ""),
                last_name=basic_data.get("last_name", ""),
                gender=Gender(basic_data.get("gender", "other")),
                date_of_birth=date_of_birth,
                city=basic_data.get("city", ""),
                online=False
            )
            session.add(new_profile)
            await session.commit()
            await session.refresh(new_profile)
            
            logger.info(f"[SAGA {saga_id}] Basic profile created: {new_profile.id}")
            
            # Возвращаем данные с правильной сериализацией
            return {
                "status": "success",
                "basic_profile_id": new_profile.id,
                "keycloak_id": keycloak_id,
                "first_name": basic_data.get("first_name"),
                "last_name": basic_data.get("last_name"),
                "gender": basic_data.get("gender"),
                "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
                "city": basic_data.get("city")
            }
    
    async def handle_create_detailed_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Создание детального профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        detailed_data = payload.get("detailed_data", {})
        
        # Получаем basic_profile_id из контекста
        create_step_result = context.get("create_basic_profile", {})
        basic_profile_id = create_step_result.get("basic_profile_id")
        keycloak_id = create_step_result.get("keycloak_id")
        
        if not basic_profile_id:
            step_result = await self._get_step_result(saga_id, "create_basic_profile")
            basic_profile_id = step_result.get("basic_profile_id")
            keycloak_id = step_result.get("keycloak_id")
        
        if not basic_profile_id:
            error_msg = f"[SAGA {saga_id}] Cannot create detailed profile: missing basic_profile_id"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] Creating detailed profile for basic_profile_id: {basic_profile_id}")
        
        async with async_session_factory() as session:
            # Проверяем, не существует ли уже детальный профиль
            stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic_profile_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"[SAGA {saga_id}] Detailed profile already exists for {basic_profile_id}")
                return {
                    "status": "success",
                    "detailed_profile_id": existing.id,
                    "already_exists": True
                }
            
            # Создаем детальный профиль
            new_detailed = DetailedProfile(
                basic_profile_id=basic_profile_id,
                about_me=detailed_data.get("about_me", ""),
                education=detailed_data.get("education", ""),
                hobbies=detailed_data.get("hobbies", ""),
                partner_preferences=detailed_data.get("partner_preferences", "")
            )
            session.add(new_detailed)
            await session.commit()
            await session.refresh(new_detailed)
            
            logger.info(f"[SAGA {saga_id}] Detailed profile created: {new_detailed.id}")
            
            return {
                "status": "success",
                "detailed_profile_id": new_detailed.id,
                "basic_profile_id": basic_profile_id,
                "keycloak_id": keycloak_id
            }
    
    async def handle_update_basic_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление базового профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        update_data = payload.get("update_data", {})
        
        logger.info(f"[SAGA {saga_id}] Updating basic profile for user: {keycloak_id}")
        
        if not update_data:
            logger.warning(f"[SAGA {saga_id}] Empty update data for {keycloak_id}")
            return {"status": "success", "updated": False, "reason": "no_data"}
        
        async with async_session_factory() as session:
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                error_msg = f"Basic profile not found for {keycloak_id}"
                logger.error(f"[SAGA {saga_id}] {error_msg}")
                raise Exception(error_msg)
            
            # Обновляем поля
            updated_fields = []
            result_data = {}
            
            if 'first_name' in update_data:
                profile.first_name = update_data['first_name']
                updated_fields.append('first_name')
                result_data['first_name'] = update_data['first_name']
            
            if 'last_name' in update_data:
                profile.last_name = update_data['last_name']
                updated_fields.append('last_name')
                result_data['last_name'] = update_data['last_name']
            
            if 'gender' in update_data:
                profile.gender = Gender(update_data['gender'])
                updated_fields.append('gender')
                result_data['gender'] = update_data['gender']
            
            if 'date_of_birth' in update_data:
                if isinstance(update_data['date_of_birth'], str):
                    profile.date_of_birth = datetime.fromisoformat(update_data['date_of_birth']).date()
                else:
                    profile.date_of_birth = update_data['date_of_birth']
                updated_fields.append('date_of_birth')
                result_data['date_of_birth'] = profile.date_of_birth.isoformat() if profile.date_of_birth else None
            
            if 'city' in update_data:
                profile.city = update_data['city']
                updated_fields.append('city')
                result_data['city'] = update_data['city']
            
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Basic profile updated: {updated_fields}")
            
            return {
                "status": "success",
                "basic_profile_id": profile.id,
                "keycloak_id": keycloak_id,
                "updated_fields": updated_fields,
                "updated_data": result_data
            }
    
    async def handle_update_detailed_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Обновление детального профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        update_data = payload.get("update_data", {})
        
        logger.info(f"[SAGA {saga_id}] Updating detailed profile for user: {keycloak_id}")
        
        if not update_data:
            logger.warning(f"[SAGA {saga_id}] Empty update data for {keycloak_id}")
            return {"status": "success", "updated": False, "reason": "no_data"}
        
        async with async_session_factory() as session:
            # Сначала находим базовый профиль
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            basic = result.scalar_one_or_none()
            
            if not basic:
                error_msg = f"Basic profile not found for {keycloak_id}"
                logger.error(f"[SAGA {saga_id}] {error_msg}")
                raise Exception(error_msg)
            
            # Находим детальный профиль
            stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic.id)
            result = await session.execute(stmt)
            detailed = result.scalar_one_or_none()
            
            if not detailed:
                # Если детального профиля нет, создаем новый
                logger.info(f"[SAGA {saga_id}] Detailed profile not found, creating new one")
                new_detailed = DetailedProfile(
                    basic_profile_id=basic.id,
                    about_me=update_data.get("about_me", ""),
                    education=update_data.get("education", ""),
                    hobbies=update_data.get("hobbies", ""),
                    partner_preferences=update_data.get("partner_preferences", "")
                )
                session.add(new_detailed)
                await session.commit()
                await session.refresh(new_detailed)
                
                logger.info(f"[SAGA {saga_id}] New detailed profile created during update")
                
                return {
                    "status": "success",
                    "detailed_profile_id": new_detailed.id,
                    "basic_profile_id": basic.id,
                    "keycloak_id": keycloak_id,
                    "created": True,
                    "updated_fields": list(update_data.keys())
                }
            
            # Обновляем существующий детальный профиль
            updated_fields = []
            if 'about_me' in update_data:
                detailed.about_me = update_data['about_me']
                updated_fields.append('about_me')
            if 'education' in update_data:
                detailed.education = update_data['education']
                updated_fields.append('education')
            if 'hobbies' in update_data:
                detailed.hobbies = update_data['hobbies']
                updated_fields.append('hobbies')
            if 'partner_preferences' in update_data:
                detailed.partner_preferences = update_data['partner_preferences']
                updated_fields.append('partner_preferences')
            
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Detailed profile updated: {updated_fields}")
            
            return {
                "status": "success",
                "detailed_profile_id": detailed.id,
                "basic_profile_id": basic.id,
                "keycloak_id": keycloak_id,
                "updated_fields": updated_fields
            }
    
    async def handle_delete_basic_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Удаление базового профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        keycloak_id = payload.get("keycloak_id")
        
        logger.info(f"[SAGA {saga_id}] Deleting profile for user: {keycloak_id}")
        
        async with async_session_factory() as session:
            stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            result = await session.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                logger.warning(f"[SAGA {saga_id}] Profile not found for {keycloak_id}")
                return {"status": "success", "deleted": False, "reason": "not_found"}
            
            await session.delete(profile)
            await session.commit()
            
            logger.info(f"[SAGA {saga_id}] Profile deleted: {keycloak_id}")
            
            return {
                "status": "success",
                "keycloak_id": keycloak_id,
                "deleted": True
            }
    
    # ========== ШАГИ ПУБЛИКАЦИИ СОБЫТИЙ ==========
    
    async def handle_publish_profile_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация события о создании профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        logger.info(f"[SAGA {saga_id}] Publishing PROFILE_CREATED event")
        
        # Получаем данные из контекста
        create_step = context.get("create_basic_profile", {})
        keycloak_id = create_step.get("keycloak_id")
        first_name = create_step.get("first_name")
        last_name = create_step.get("last_name")
        
        if not keycloak_id:
            step_result = await self._get_step_result(saga_id, "create_basic_profile")
            keycloak_id = step_result.get("keycloak_id")
            first_name = step_result.get("first_name")
            last_name = step_result.get("last_name")
        
        if not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        # Публикуем событие обновления профиля (для chat-service и других)
        success = await event_service.publish_profile_updated(
            keycloak_id=keycloak_id,
            updated_fields={
                "first_name": first_name,
                "last_name": last_name,
                "profile_created": True
            },
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish PROFILE_CREATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Также отправляем запрос на обновление имени в Keycloak
        if first_name or last_name:
            name_update = {}
            if first_name:
                name_update["first_name"] = first_name
            if last_name:
                name_update["last_name"] = last_name
            
            await event_service.publish_keycloak_update_requested(
                keycloak_id=keycloak_id,
                first_name=first_name,
                last_name=last_name,
                correlation_id=saga_id
            )
        
        logger.info(f"[SAGA {saga_id}] PROFILE_CREATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_profile_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация события об обновлении профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing PROFILE_UPDATED event")
        
        keycloak_id = payload.get("keycloak_id")
        updated_fields = payload.get("updated_fields", {})
        
        if not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        # Публикуем событие обновления профиля
        success = await event_service.publish_profile_updated(
            keycloak_id=keycloak_id,
            updated_fields=updated_fields,
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish PROFILE_UPDATED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Если обновились имя или фамилия, отправляем запрос в Keycloak
        if 'first_name' in updated_fields or 'last_name' in updated_fields:
            name_update = {}
            if 'first_name' in updated_fields:
                name_update["first_name"] = updated_fields['first_name']
            if 'last_name' in updated_fields:
                name_update["last_name"] = updated_fields['last_name']
            
            await event_service.publish_keycloak_update_requested(
                keycloak_id=keycloak_id,
                first_name=name_update.get("first_name"),
                last_name=name_update.get("last_name"),
                correlation_id=saga_id
            )
        
        logger.info(f"[SAGA {saga_id}] PROFILE_UPDATED event published")
        return {"status": "success", "event_published": True}
    
    async def handle_publish_profile_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг: Публикация события об удалении профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        
        logger.info(f"[SAGA {saga_id}] Publishing PROFILE_DELETED event")
        
        keycloak_id = payload.get("keycloak_id")
        
        if not keycloak_id:
            error_msg = f"[SAGA {saga_id}] Missing keycloak_id for event publication"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        from app.services.event_service import get_event_service
        event_service = get_event_service()
        
        # Публикуем событие удаления профиля
        success = await event_service.publish_profile_updated(
            keycloak_id=keycloak_id,
            updated_fields={"profile_deleted": True},
            correlation_id=saga_id
        )
        
        if not success:
            error_msg = f"[SAGA {saga_id}] Failed to publish PROFILE_DELETED event"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"[SAGA {saga_id}] PROFILE_DELETED event published")
        return {"status": "success", "event_published": True}
    
    # ========== КОМПЕНСАЦИИ ==========
    
    async def handle_compensate_create_basic_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Компенсация: удаление базового профиля"""
        payload = data.get("payload", {})
        saga_id = data.get("saga_id")
        context = data.get("context", {})
        
        create_step_result = context.get("create_basic_profile", {})
        basic_profile_id = create_step_result.get("basic_profile_id")
        keycloak_id = create_step_result.get("keycloak_id")
        
        if not basic_profile_id:
            basic_profile_id = payload.get("basic_profile_id")
            keycloak_id = payload.get("keycloak_id")
        
        if not basic_profile_id and not keycloak_id:
            logger.warning(f"[SAGA {saga_id}] No profile identifier for compensation")
            return {"status": "success", "reason": "no_identifier"}
        
        logger.info(f"[SAGA {saga_id}] Compensating: deleting profile")
        
        async with async_session_factory() as session:
            if basic_profile_id:
                stmt = select(BasicProfile).where(BasicProfile.id == basic_profile_id)
            else:
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
            
            result = await session.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if profile:
                await session.delete(profile)
                await session.commit()
                logger.info(f"[SAGA {saga_id}] Profile deleted during compensation")
                return {"status": "success", "deleted": True}
            else:
                logger.warning(f"[SAGA {saga_id}] Profile not found during compensation")
                return {"status": "success", "deleted": False}