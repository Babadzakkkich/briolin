from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database.models import SearchSession
from app.schemas.search import (
    SearchRequest,
    TargetedSearchRequest,
    SearchResponse,
    SearchSessionInfo,
    ProfilePreviewResponse,
    SearchLockInfo,
    PaginationInfo
)
from app.services.profile_service_client import ProfileServiceClient
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    DatabaseException,
    SearchSessionNotFoundException,
    InvalidSearchParametersException,
    SearchLockedException
)
from app.utils.age_calculator import calculate_age_from_birth_date


class SearchService:
    def __init__(self, db: AsyncSession, profile_client: ProfileServiceClient):
        self.db = db
        self.profile_client = profile_client

    async def _check_targeted_search_lock(self, keycloak_id: str) -> Tuple[
        bool, Optional[datetime], int, Optional[SearchSession]]:
        """Проверяет, заблокирован ли таргетированный поиск для пользователя"""
        try:
            lock_period = datetime.utcnow() - timedelta(hours=settings.targeted_search_lock_hours)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.keycloak_id == keycloak_id,
                    SearchSession.search_type == 'targeted',
                    SearchSession.created_at >= lock_period
                )
            ).order_by(SearchSession.created_at.desc())

            result = await self.db.execute(stmt)
            recent_sessions = result.scalars().all()

            if not recent_sessions:
                return False, None, 0, None

            total_viewed = 0
            for session in recent_sessions:
                if session.viewed_profile_ids:
                    total_viewed += len(session.viewed_profile_ids)

            last_session = recent_sessions[0] if recent_sessions else None

            if total_viewed >= settings.profiles_per_page:
                first_session = recent_sessions[-1]
                unlock_time = first_session.created_at + timedelta(hours=settings.targeted_search_lock_hours)

                if unlock_time > datetime.utcnow():
                    return True, unlock_time, total_viewed, last_session

            return False, None, total_viewed, last_session

        except Exception as e:
            logger.error(f"Error checking search lock for keycloak_id {keycloak_id}: {str(e)}")
            return False, None, 0, None

    async def _get_existing_session(
            self,
            keycloak_id: str,
            search_type: str,
            filters: Dict[str, Any]
    ) -> Optional[SearchSession]:
        """Проверяет, существует ли активная сессия с такими же фильтрами"""
        try:
            day_ago = datetime.utcnow() - timedelta(days=1)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.keycloak_id == keycloak_id,
                    SearchSession.search_type == search_type,
                    SearchSession.created_at >= day_ago
                )
            ).order_by(SearchSession.created_at.desc())

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            for session in sessions:
                if session.filters == filters:
                    return session

            return None

        except Exception as e:
            logger.error(f"Error checking existing session: {str(e)}")
            return None

    async def _get_profiles_by_keycloak_ids(
            self,
            keycloak_ids: List[str],
            include_detailed: bool = False
    ) -> List[ProfilePreviewResponse]:
        """
        Получает детальную информацию о профилях по их Keycloak ID через profile-service
        """
        if not keycloak_ids:
            return []

        try:
            profiles_data = await self.profile_client.get_profiles_batch(keycloak_ids)

            result_profiles = []
            for profile in profiles_data:
                basic = profile.get("basic", {})
                detailed = profile.get("detailed")

                birth_date_str = basic.get("date_of_birth")
                age = 0
                if birth_date_str:
                    try:
                        birth_date = datetime.fromisoformat(birth_date_str).date()
                        age = calculate_age_from_birth_date(birth_date)
                    except:
                        pass

                result_profiles.append(ProfilePreviewResponse(
                    keycloak_id=basic.get("keycloak_id", ""),
                    first_name=basic.get("first_name", ""),
                    last_name=basic.get("last_name", ""),
                    gender=basic.get("gender", ""),
                    age=age,
                    city=basic.get("city", ""),
                    online=basic.get("online", False),
                    avatar_thumbnail_url=basic.get("thumbnail_url"),
                    education=detailed.get("education") if detailed else None,
                    hobbies=detailed.get("hobbies") if detailed else None,
                    about_me=detailed.get("about_me") if detailed else None,
                    partner_preferences=detailed.get("partner_preferences") if detailed else None
                ))

            return result_profiles

        except Exception as e:
            logger.error(f"Error getting profiles by keycloak ids: {str(e)}")
            return []

    async def _perform_search(
        self,
        keycloak_id: str,
        search_type: str,
        filters: Dict[str, Any]
    ) -> Tuple[List[ProfilePreviewResponse], List[str], int, int]:
        """
        Выполняет поиск через profile-service
        Возвращает: (профили, Keycloak ID профилей, общее количество, количество страниц)
        """
        try:
            search_params = {
                "gender": filters.get("gender"),
                "min_age": filters.get("min_age"),
                "max_age": filters.get("max_age"),
                "city": filters.get("city"),
                "education": filters.get("education"),
                "hobbies_keywords": filters.get("hobbies_keywords"),
                "partner_preferences": filters.get("partner_preferences"),
                "online_only": filters.get("online_only", False),
                "exclude_keycloak_id": keycloak_id,
                "page": filters.get("page", 1),
                "limit": filters.get("limit", 10)
            }

            result = await self.profile_client.search_profiles(search_params)

            if not result:
                return [], [], 0, 1

            profiles_data = result.get("profiles", [])
            total = result.get("total", 0)
            total_pages = result.get("total_pages", 1)

            profiles = []
            keycloak_ids = []
            
            for profile in profiles_data:
                basic = profile.get("basic", {})
                detailed = profile.get("detailed")

                # Получаем Keycloak ID
                profile_keycloak_id = basic.get("keycloak_id") or profile.get("keycloak_id")
                if profile_keycloak_id:
                    keycloak_ids.append(profile_keycloak_id)

                birth_date_str = basic.get("date_of_birth")
                age = 0
                if birth_date_str:
                    try:
                        birth_date = datetime.fromisoformat(birth_date_str).date()
                        age = calculate_age_from_birth_date(birth_date)
                    except:
                        pass

                profiles.append(ProfilePreviewResponse(
                    keycloak_id=profile_keycloak_id,
                    first_name=basic.get("first_name", ""),
                    last_name=basic.get("last_name", ""),
                    gender=basic.get("gender", ""),
                    age=age,
                    city=basic.get("city", ""),
                    online=basic.get("online", False),
                    avatar_thumbnail_url=basic.get("thumbnail_url"),
                    education=detailed.get("education") if detailed else None,
                    hobbies=detailed.get("hobbies") if detailed else None,
                    about_me=detailed.get("about_me") if detailed else None,
                    partner_preferences=detailed.get("partner_preferences") if detailed else None
                ))

            return profiles, keycloak_ids, total, total_pages

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], [], 0, 1

    async def _get_profiles_page_from_session(
        self,
        session: SearchSession,
        page: int,
        limit: int
    ) -> Tuple[List[ProfilePreviewResponse], bool, bool]:
        """Получает страницу профилей из существующей сессии"""
        
        available_ids = session.remaining_profile_ids
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        if start_idx >= len(available_ids):
            return [], False, page > 1
        
        page_ids = available_ids[start_idx:end_idx]
        
        profiles = await self._get_profiles_by_keycloak_ids(
            page_ids, 
            include_detailed=(session.search_type == 'targeted')
        )
        
        if session.viewed_profile_ids is None:
            session.viewed_profile_ids = []
        session.viewed_profile_ids.extend(page_ids)
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        
        has_next = end_idx < len(available_ids)
        has_previous = page > 1
        
        return profiles, has_next, has_previous

    async def classic_search(
        self,
        keycloak_id: str,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        city: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> SearchResponse:
        """Выполняет классический поиск по профилям"""
        if min_age and max_age and min_age > max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        search_filters = {
            "search_type": "classic",
            "search_timestamp": datetime.utcnow().isoformat()
        }

        if gender:
            search_filters["gender"] = gender
        if min_age is not None:
            search_filters["min_age"] = min_age
        if max_age is not None:
            search_filters["max_age"] = max_age
        if city:
            search_filters["city"] = city
        search_filters["page"] = page
        search_filters["limit"] = limit

        try:
            existing_session = await self._get_existing_session(keycloak_id, "classic", search_filters)

            if existing_session:
                logger.info(f"Found existing search session {existing_session.id} for user {keycloak_id}")
                
                profiles, has_next, has_previous = await self._get_profiles_page_from_session(
                    existing_session, page, limit
                )
                
                # Создаем объект пагинации
                pagination = PaginationInfo(
                    current_page=page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    page_size=limit
                )
                
                return SearchResponse(
                    search_session_id=existing_session.id,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    pagination=pagination,
                    lock_info=None  # Для классического поиска нет блокировки
                )

            # Выполняем новый поиск
            profiles, keycloak_ids, total, total_pages = await self._perform_search(
                keycloak_id=keycloak_id,
                search_type="classic",
                filters=search_filters
            )

            start_idx = 0
            end_idx = min(limit, len(keycloak_ids))
            first_page_ids = keycloak_ids[start_idx:end_idx]
            
            # Получаем профили для первой страницы с keycloak_id
            first_page_profiles = []
            for profile in profiles[:end_idx]:
                # Добавляем keycloak_id в профили (он уже должен быть в данных от profile-service)
                first_page_profiles.append(profile)

            # Сохраняем сессию
            search_session = SearchSession(
                keycloak_id=keycloak_id,
                search_type='classic',
                filters=search_filters,
                result_profile_ids=keycloak_ids,
                viewed_profile_ids=first_page_ids,
                total_results=total
            )
            self.db.add(search_session)
            await self.db.commit()
            await self.db.refresh(search_session)

            # Создаем объект пагинации
            pagination = PaginationInfo(
                current_page=page,
                total_pages=total_pages,
                total_results=total,
                page_size=limit
            )

            return SearchResponse(
                search_session_id=search_session.id,
                profiles=first_page_profiles,
                filters=search_filters,
                created_at=search_session.created_at,
                pagination=pagination,
                lock_info=None  # Для классического поиска нет блокировки
            )

        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Search failed for user {keycloak_id}: {str(e)}")
            raise DatabaseException(f"Search failed: {str(e)}")


    async def targeted_search(
        self,
        keycloak_id: str,
        search_params: TargetedSearchRequest
    ) -> SearchResponse:
        """Выполняет таргетированный поиск с блокировкой"""
        if search_params.min_age and search_params.max_age and search_params.min_age > search_params.max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        try:
            # Проверяем блокировку
            is_locked, unlock_time, total_viewed, last_session = await self._check_targeted_search_lock(keycloak_id)

            if is_locked:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())
                raise SearchLockedException(
                    message=f"Targeted search is locked. You've viewed {total_viewed} profiles. "
                            f"Next search available in {time_until_unlock // 60} minutes",
                    unlock_time=unlock_time,
                    time_until_unlock=time_until_unlock,
                    profiles_viewed=total_viewed
                )

            # Формируем фильтры
            search_filters = {
                "search_type": "targeted",
                "search_timestamp": datetime.utcnow().isoformat()
            }

            params_dict = search_params.model_dump(exclude_none=True)
            for key, value in params_dict.items():
                if key not in ['page', 'limit']:
                    if isinstance(value, list):
                        if value:
                            search_filters[key] = value
                    elif value is not None and value != "":
                        search_filters[key] = value

            search_filters["page"] = search_params.page
            search_filters["limit"] = search_params.limit

            # Проверяем существующую сессию
            existing_session = await self._get_existing_session(keycloak_id, "targeted", search_filters)

            if existing_session:
                logger.info(f"Found existing targeted session {existing_session.id} for user {keycloak_id}")

                profiles, has_next, has_previous = await self._get_profiles_page_from_session(
                    existing_session, search_params.page, search_params.limit
                )
                
                # Проверяем блокировку после обновления
                is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(keycloak_id)
                
                # Создаем объект пагинации
                pagination = PaginationInfo(
                    current_page=search_params.page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    page_size=search_params.limit
                )
                
                # Создаем объект информации о блокировке
                lock_info = None
                if is_locked:
                    lock_info = SearchLockInfo(
                        is_locked=True,
                        profiles_viewed=new_total_viewed,
                        locked_until=unlock_time,
                        time_until_unlock=int((unlock_time - datetime.utcnow()).total_seconds()) if unlock_time else None
                    )
                
                return SearchResponse(
                    search_session_id=existing_session.id,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    pagination=pagination,
                    lock_info=lock_info
                )

            # Выполняем новый поиск
            profiles, keycloak_ids, total, total_pages = await self._perform_search(
                keycloak_id=keycloak_id,
                search_type="targeted",
                filters=search_filters
            )

            # Пагинация для первой страницы
            start_idx = 0
            end_idx = min(search_params.limit, len(keycloak_ids))
            first_page_ids = keycloak_ids[start_idx:end_idx]
            
            # Получаем профили для первой страницы
            first_page_profiles = await self._get_profiles_by_keycloak_ids(first_page_ids, include_detailed=True)

            # Сохраняем сессию
            search_session = SearchSession(
                keycloak_id=keycloak_id,
                search_type='targeted',
                filters=search_filters,
                result_profile_ids=keycloak_ids,
                viewed_profile_ids=first_page_ids,
                total_results=total
            )
            self.db.add(search_session)
            await self.db.commit()
            await self.db.refresh(search_session)

            # Проверяем блокировку после создания сессии
            is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(keycloak_id)

            # Создаем объект пагинации
            pagination = PaginationInfo(
                current_page=search_params.page,
                total_pages=total_pages,
                total_results=total,
                page_size=search_params.limit
            )
            
            # Создаем объект информации о блокировке
            lock_info = None
            if is_locked:
                lock_info = SearchLockInfo(
                    is_locked=True,
                    profiles_viewed=new_total_viewed,
                    locked_until=unlock_time,
                    time_until_unlock=int((unlock_time - datetime.utcnow()).total_seconds()) if unlock_time else None
                )

            return SearchResponse(
                search_session_id=search_session.id,
                profiles=first_page_profiles,
                filters=search_filters,
                created_at=search_session.created_at,
                pagination=pagination,
                lock_info=lock_info
            )

        except SearchLockedException:
            raise
        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Targeted search failed for user {keycloak_id}: {str(e)}")
            raise DatabaseException(f"Targeted search failed: {str(e)}")

    async def get_search_lock_status(self, keycloak_id: str) -> SearchLockInfo:  # Изменен тип возврата
        """Получает статус блокировки поиска для пользователя"""
        try:
            is_locked, unlock_time, total_viewed, _ = await self._check_targeted_search_lock(keycloak_id)

            time_until_unlock = None
            if unlock_time:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())

            return SearchLockInfo(
                is_locked=is_locked,
                profiles_viewed=total_viewed,
                locked_until=unlock_time,
                time_until_unlock=time_until_unlock
            )
        except Exception as e:
            logger.error(f"Failed to get search lock status for user {keycloak_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search lock status: {str(e)}")

    async def get_search_history(
        self,
        keycloak_id: str,
        limit: int = 50,
        search_type: Optional[str] = None
    ) -> List[SearchSessionInfo]:
        """Получение истории поисковых сессий пользователя"""
        try:
            stmt = select(SearchSession).where(SearchSession.keycloak_id == keycloak_id)

            if search_type:
                stmt = stmt.where(SearchSession.search_type == search_type)

            stmt = stmt.order_by(SearchSession.created_at.desc()).limit(limit)

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            return [
                SearchSessionInfo(
                    search_session_id=session.id,
                    search_type=session.search_type,
                    filters=session.filters,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    total_results=session.total_results,
                    profiles_viewed=len(session.viewed_profile_ids) if session.viewed_profile_ids else 0,
                    profiles_remaining=len(session.remaining_profile_ids)
                )
                for session in sessions
            ]
        except Exception as e:
            logger.error(f"Failed to get search history for user {keycloak_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search history: {str(e)}")

    async def get_search_session(self, session_id: int, keycloak_id: str) -> SearchSessionInfo:  # Изменен тип возврата
        """Получение конкретной поисковой сессии"""
        try:
            stmt = select(SearchSession).where(
                and_(
                    SearchSession.id == session_id,
                    SearchSession.keycloak_id == keycloak_id
                )
            )
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                raise SearchSessionNotFoundException(f"Search session {session_id} not found")

            return SearchSessionInfo(
                search_session_id=session.id,
                search_type=session.search_type,
                filters=session.filters,
                created_at=session.created_at,
                updated_at=session.updated_at,
                total_results=session.total_results,
                profiles_viewed=len(session.viewed_profile_ids) if session.viewed_profile_ids else 0,
                profiles_remaining=len(session.remaining_profile_ids)
            )
        except SearchSessionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get search session {session_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search session: {str(e)}")

    async def get_profiles_count(self) -> int:
        """Получение общего количества профилей через profile-service"""
        try:
            return await self.profile_client.get_profiles_count()
        except Exception as e:
            logger.error(f"Failed to get profiles count: {str(e)}")
            raise DatabaseException(f"Failed to get profiles count: {str(e)}")

    async def delete_search_history(self, keycloak_id: str, older_than_days: int = 30) -> int:
        """Удаление старой истории поиска"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.keycloak_id == keycloak_id,
                    SearchSession.created_at < cutoff_date
                )
            )

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            for session in sessions:
                await self.db.delete(session)

            await self.db.commit()

            deleted_count = len(sessions)
            logger.info(f"Deleted {deleted_count} old search sessions for user {keycloak_id}")

            return deleted_count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete search history for user {keycloak_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete search history: {str(e)}")