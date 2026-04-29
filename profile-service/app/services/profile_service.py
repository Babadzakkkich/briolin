import uuid
from datetime import date, datetime
from sqlalchemy import select, func
from typing import Dict, Any, Optional, Tuple, List

import sqlalchemy

from app.database.models import BasicProfile, DetailedProfile
from app.database.session import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.profile import (
    BasicProfileCreate, BasicProfileResponse, DetailedProfileCreate, DetailedProfileResponse, FullProfileResponse, FullProfileUpdate
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
    async def create_basic_profile(
        self,
        keycloak_id: str,
        basic_data: BasicProfileCreate,
        current_user: dict
    ) -> FullProfileResponse:
        """
        СИНХРОННОЕ создание базового профиля
        Возвращает созданный профиль с кодом 201
        """
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionDeniedException("Cannot create profile for another user")
        
        # Проверяем существование профиля
        existing = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if existing:
            logger.info(f"Basic profile already exists for {keycloak_id}")
            # Возвращаем существующий профиль
            return await self.get_full_profile_by_keycloak_id(keycloak_id)
        
        # Создаем базовый профиль
        new_profile = BasicProfile(
            keycloak_id=keycloak_id,
            first_name=basic_data.first_name,
            last_name=basic_data.last_name,
            gender=basic_data.gender,
            date_of_birth=basic_data.date_of_birth,
            city=basic_data.city,
            online=False
        )
        
        self.db.add(new_profile)
        await self.db.commit()
        await self.db.refresh(new_profile)
        
        logger.info(f"Basic profile created: {new_profile.id} for user {keycloak_id}")
        
        # Публикуем событие о создании профиля (асинхронно, не блокируя ответ)
        try:
            await self.event_service.publish_profile_updated(
                keycloak_id=keycloak_id,
                updated_fields={
                    "first_name": basic_data.first_name,
                    "last_name": basic_data.last_name,
                    "profile_created": True
                }
            )
            
            # Отправляем запрос на обновление имени в Keycloak
            await self.event_service.publish_keycloak_update_requested(
                keycloak_id=keycloak_id,
                first_name=basic_data.first_name,
                last_name=basic_data.last_name
            )
        except Exception as e:
            # Логируем ошибку публикации, но не блокируем ответ
            logger.error(f"Failed to publish profile created event: {e}")
        
        # Возвращаем полный профиль
        return await self.get_full_profile_by_keycloak_id(keycloak_id)


    async def create_detailed_profile(
        self,
        keycloak_id: str,
        detailed_data: DetailedProfileCreate,
        current_user: dict
    ) -> FullProfileResponse:
        """
        СИНХРОННОЕ создание детального профиля
        Возвращает полный профиль с кодом 201
        """
        # Проверяем права пользователя
        if current_user["keycloak_id"] != keycloak_id:
            raise PermissionDeniedException("Cannot create profile for another user")
        
        # Проверяем существование базового профиля
        basic_profile = await self._get_basic_profile_by_keycloak_id(keycloak_id)
        if not basic_profile:
            raise ProfileNotFoundException("Basic profile not found. Create basic profile first.")
        
        # Проверяем, существует ли уже детальный профиль
        stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic_profile.id)
        result = await self.db.execute(stmt)
        existing_detailed = result.scalar_one_or_none()
        
        if existing_detailed:
            logger.info(f"Detailed profile already exists for {keycloak_id}")
            # Возвращаем существующий полный профиль
            return await self.get_full_profile_by_keycloak_id(keycloak_id)
        
        # Создаем детальный профиль
        new_detailed = DetailedProfile(
            basic_profile_id=basic_profile.id,
            about_me=detailed_data.about_me,
            education=detailed_data.education,
            hobbies=detailed_data.hobbies,
            partner_preferences=detailed_data.partner_preferences
        )
        
        self.db.add(new_detailed)
        await self.db.commit()
        await self.db.refresh(new_detailed)
        
        logger.info(f"Detailed profile created: {new_detailed.id} for user {keycloak_id}")
        
        # Публикуем событие об обновлении профиля (добавлен детальный)
        try:
            await self.event_service.publish_profile_updated(
                keycloak_id=keycloak_id,
                updated_fields={"detailed_profile_created": True}
            )
        except Exception as e:
            logger.error(f"Failed to publish profile updated event: {e}")
        
        # Возвращаем полный профиль
        return await self.get_full_profile_by_keycloak_id(keycloak_id)
    
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

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    async def _get_basic_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[BasicProfile]:
        """Получение базового профиля по keycloak_id (внутренний метод)"""
        stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_full_profile_by_keycloak_id(self, keycloak_id: str) -> FullProfileResponse:
        """Получение полного профиля по keycloak_id"""
        stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        basic = result.scalar_one_or_none()
        
        if not basic:
            raise ProfileNotFoundException(f"Profile not found for keycloak_id {keycloak_id}")
        
        stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic.id)
        result = await self.db.execute(stmt)
        detailed = result.scalar_one_or_none()
        
        # Преобразуем BasicProfile в BasicProfileResponse
        basic_response = BasicProfileResponse(
            id=basic.id,
            keycloak_id=basic.keycloak_id,
            first_name=basic.first_name,
            last_name=basic.last_name,
            gender=basic.gender,
            date_of_birth=basic.date_of_birth,
            city=basic.city,
            online=basic.online,
            avatar_url=basic.avatar_url,
            thumbnail_url=basic.thumbnail_url,
            created_at=basic.created_at,
            updated_at=basic.updated_at,
            last_login_at=basic.last_login_at
        )
        
        # Преобразуем DetailedProfile в DetailedProfileResponse если есть
        detailed_response = None
        if detailed:
            detailed_response = DetailedProfileResponse(
                id=detailed.id,
                about_me=detailed.about_me,
                education=detailed.education,
                hobbies=detailed.hobbies,
                partner_preferences=detailed.partner_preferences
            )
        
        return FullProfileResponse(
            basic=basic_response,
            detailed=detailed_response
        )

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
    
# ========== МЕТОДЫ ДЛЯ SEARCH-SERVICE ==========

    async def get_profiles_batch(self, profile_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Получение нескольких профилей по их ID
        Используется search-service для batch-запроса
        """
        if not profile_ids:
            return []
        
        try:
            # Получаем базовые профили
            stmt = select(BasicProfile).where(BasicProfile.id.in_(profile_ids))
            result = await self.db.execute(stmt)
            basic_profiles = result.scalars().all()
            
            if not basic_profiles:
                return []
            
            # Получаем ID для запроса детальных профилей
            basic_ids = [p.id for p in basic_profiles]
            
            # Получаем детальные профили
            detailed_stmt = select(DetailedProfile).where(
                DetailedProfile.basic_profile_id.in_(basic_ids)
            )
            detailed_result = await self.db.execute(detailed_stmt)
            detailed_profiles = {dp.basic_profile_id: dp for dp in detailed_result.scalars().all()}
            
            # Формируем ответ
            result_profiles = []
            for profile in basic_profiles:
                profile_data = {
                    "basic": {
                        "id": profile.id,
                        "keycloak_id": profile.keycloak_id,
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "gender": profile.gender.value if hasattr(profile.gender, 'value') else profile.gender,
                        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                        "city": profile.city,
                        "online": profile.online,
                        "avatar_url": profile.avatar_url,
                        "thumbnail_url": profile.thumbnail_url,
                        "created_at": profile.created_at.isoformat() if profile.created_at else None,
                        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                        "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
                    }
                }
                
                detailed = detailed_profiles.get(profile.id)
                if detailed:
                    profile_data["detailed"] = {
                        "id": detailed.id,
                        "about_me": detailed.about_me,
                        "education": detailed.education,
                        "hobbies": detailed.hobbies,
                        "partner_preferences": detailed.partner_preferences
                    }
                else:
                    profile_data["detailed"] = None
                
                result_profiles.append(profile_data)
            
            return result_profiles
            
        except Exception as e:
            logger.error(f"Failed to get profiles batch: {e}")
            raise DatabaseException(f"Failed to get profiles batch: {str(e)}")


    async def get_profiles_count(self) -> int:
        """
        Получение общего количества профилей
        Используется search-service для статистики
        """
        try:
            stmt = select(func.count()).select_from(BasicProfile)
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get profiles count: {e}")
            raise DatabaseException(f"Failed to get profiles count: {str(e)}")


    async def check_profiles_exist(self, profile_ids: List[int]) -> Dict[int, bool]:
        """
        Проверка существования профилей по их ID
        Используется search-service для валидации
        """
        if not profile_ids:
            return {}
        
        try:
            stmt = select(BasicProfile.id).where(BasicProfile.id.in_(profile_ids))
            result = await self.db.execute(stmt)
            existing_ids = {row[0] for row in result.all()}
            
            return {pid: pid in existing_ids for pid in profile_ids}
        except Exception as e:
            logger.error(f"Failed to check profiles exist: {e}")
            raise DatabaseException(f"Failed to check profiles exist: {str(e)}")


    async def search_profiles(
        self,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        city: Optional[str] = None,
        education: Optional[str] = None,
        hobbies_keywords: Optional[List[str]] = None,
        partner_preferences: Optional[str] = None,
        online_only: bool = False,
        exclude_user_id: Optional[int] = None,
        exclude_keycloak_id: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Поиск профилей с фильтрацией
        Основной метод для search-service
        """
        try:
            # Базовый запрос
            query = select(BasicProfile)
            
            # Присоединяем DetailedProfile если нужны фильтры по нему
            if education or hobbies_keywords or partner_preferences:
                query = query.outerjoin(
                    DetailedProfile,
                    BasicProfile.id == DetailedProfile.basic_profile_id
                )
            
            # Условия фильтрации
            conditions = []
            
            if gender:
                conditions.append(BasicProfile.gender == gender)
            
            if city:
                conditions.append(BasicProfile.city.ilike(f"%{city}%"))
            
            if online_only:
                conditions.append(BasicProfile.online == True)
            
            if exclude_user_id:
                conditions.append(BasicProfile.id != exclude_user_id)
            
            if exclude_keycloak_id:
                conditions.append(BasicProfile.keycloak_id != exclude_keycloak_id)
            
            # Возрастная фильтрация
            if min_age is not None or max_age is not None:
                today = datetime.utcnow().date()
                if min_age is not None:
                    min_birth_date = date(today.year - min_age - 1, today.month, today.day)
                    conditions.append(BasicProfile.date_of_birth <= min_birth_date)
                if max_age is not None:
                    max_birth_date = date(today.year - max_age, today.month, today.day)
                    conditions.append(BasicProfile.date_of_birth >= max_birth_date)
            
            # Фильтры по detailed profile
            if education:
                conditions.append(DetailedProfile.education.ilike(f"%{education}%"))
            
            if partner_preferences:
                conditions.append(DetailedProfile.partner_preferences.ilike(f"%{partner_preferences}%"))
            
            if hobbies_keywords:
                hobby_conditions = []
                for keyword in hobbies_keywords:
                    if keyword and keyword.strip():
                        hobby_conditions.append(
                            DetailedProfile.hobbies.ilike(f"%{keyword.strip()}%")
                        )
                if hobby_conditions:
                    conditions.append(sqlalchemy.or_(*hobby_conditions))
            
            # Применяем условия
            if conditions:
                query = query.where(sqlalchemy.and_(*conditions))
            
            # Получаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0
            
            # Добавляем пагинацию
            paginated_query = query.order_by(
                BasicProfile.last_login_at.desc().nullslast(),
                BasicProfile.id
            ).offset((page - 1) * limit).limit(limit)
            
            result = await self.db.execute(paginated_query)
            profiles = result.scalars().all()
            
            # Получаем детальные профили для найденных
            if profiles:
                profile_ids = [p.id for p in profiles]
                detailed_stmt = select(DetailedProfile).where(
                    DetailedProfile.basic_profile_id.in_(profile_ids)
                )
                detailed_result = await self.db.execute(detailed_stmt)
                detailed_map = {dp.basic_profile_id: dp for dp in detailed_result.scalars().all()}
            else:
                detailed_map = {}
            
            # Формируем результат
            result_profiles = []
            for profile in profiles:
                profile_data = {
                    "basic": {
                        "id": profile.id,
                        "keycloak_id": profile.keycloak_id,
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "gender": profile.gender.value if hasattr(profile.gender, 'value') else profile.gender,
                        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                        "city": profile.city,
                        "online": profile.online,
                        "avatar_url": profile.avatar_url,  # Добавляем
                        "thumbnail_url": profile.thumbnail_url,  # Добавляем
                        "created_at": profile.created_at.isoformat() if profile.created_at else None,
                        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                        "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None
                    }
                }
                
                detailed = detailed_map.get(profile.id)
                if detailed:
                    profile_data["detailed"] = {
                        "id": detailed.id,
                        "about_me": detailed.about_me,
                        "education": detailed.education,
                        "hobbies": detailed.hobbies,
                        "partner_preferences": detailed.partner_preferences
                    }
                else:
                    profile_data["detailed"] = None
                
                result_profiles.append(profile_data)
            
            return {
                "profiles": result_profiles,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if total > 0 else 1
            }
            
        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            raise DatabaseException(f"Failed to search profiles: {str(e)}")