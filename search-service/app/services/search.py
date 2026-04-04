from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from sqlalchemy.exc import IntegrityError

from app.database.models import SearchSession, SearchLock
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

    async def _get_or_create_lock(self, keycloak_id: str) -> SearchLock:
        """
        Получает существующую блокировку или создает новую для пользователя
        """
        stmt = select(SearchLock).where(SearchLock.keycloak_id == keycloak_id)
        result = await self.db.execute(stmt)
        lock = result.scalar_one_or_none()
        
        if not lock:
            lock = SearchLock(
                keycloak_id=keycloak_id,
                is_locked=False,
                profiles_viewed=0
            )
            self.db.add(lock)
            await self.db.flush()
        
        return lock

    async def _check_and_update_lock(
        self, 
        keycloak_id: str, 
        new_views: int = 0
    ) -> Tuple[bool, Optional[datetime], int]:
        """
        Атомарная проверка и обновление блокировки.
        Использует SELECT FOR UPDATE для предотвращения race condition.
        
        Args:
            keycloak_id: ID пользователя
            new_views: Количество новых просмотренных профилей
        
        Returns:
            Tuple[is_locked, locked_until, total_viewed]
        """
        try:
            # Блокируем строку для обновления (атомарная операция)
            stmt = select(SearchLock).where(
                SearchLock.keycloak_id == keycloak_id
            ).with_for_update()
            
            result = await self.db.execute(stmt)
            lock = result.scalar_one_or_none()
            
            if not lock:
                # Создаем новую запись
                lock = SearchLock(
                    keycloak_id=keycloak_id,
                    is_locked=False,
                    profiles_viewed=0
                )
                self.db.add(lock)
                await self.db.flush()
            
            # Проверяем, не истекла ли существующая блокировка
            if lock.is_locked and lock.locked_until and lock.locked_until <= datetime.utcnow():
                # Блокировка истекла - сбрасываем
                lock.is_locked = False
                lock.profiles_viewed = 0
                lock.lock_period_start = None
                lock.locked_until = None
                logger.info(f"Lock expired for user {keycloak_id[:8]}...")
            
            # Если не заблокирован и есть новые просмотры, обновляем счетчик
            if not lock.is_locked and new_views > 0:
                # Определяем начало периода блокировки
                if not lock.lock_period_start:
                    lock.lock_period_start = datetime.utcnow()
                
                lock.profiles_viewed += new_views
                
                # Проверяем, не превышен ли лимит
                if lock.profiles_viewed >= settings.targeted_search_max_views:
                    lock.is_locked = True
                    lock.locked_until = lock.lock_period_start + timedelta(
                        hours=settings.targeted_search_lock_hours
                    )
                    logger.warning(
                        f"Targeted search locked for user {keycloak_id[:8]}... "
                        f"Viewed {lock.profiles_viewed} profiles. "
                        f"Unlock at {lock.locked_until}"
                    )
            
            await self.db.flush()
            
            return lock.is_locked, lock.locked_until, lock.profiles_viewed
            
        except Exception as e:
            logger.error(f"Error in _check_and_update_lock for {keycloak_id[:8]}...: {str(e)}")
            await self.db.rollback()
            # В случае ошибки возвращаем безопасные значения (не блокируем)
            return False, None, 0

    async def _reset_lock_if_needed(self, keycloak_id: str) -> None:
        """
        Проверяет и сбрасывает блокировку, если она истекла
        """
        try:
            stmt = select(SearchLock).where(
                and_(
                    SearchLock.keycloak_id == keycloak_id,
                    SearchLock.is_locked == True,
                    SearchLock.locked_until <= datetime.utcnow()
                )
            ).with_for_update()
            
            result = await self.db.execute(stmt)
            expired_lock = result.scalar_one_or_none()
            
            if expired_lock:
                expired_lock.is_locked = False
                expired_lock.profiles_viewed = 0
                expired_lock.lock_period_start = None
                expired_lock.locked_until = None
                await self.db.flush()
                logger.info(f"Reset expired lock for user {keycloak_id[:8]}...")
                
        except Exception as e:
            logger.error(f"Error resetting lock for {keycloak_id[:8]}...: {str(e)}")

    async def _get_existing_session(
        self,
        keycloak_id: str,
        search_type: str,
        filters: Dict[str, Any]
    ) -> Optional[SearchSession]:
        """Проверяет, существует ли активная сессия с такими же фильтрами"""
        try:
            day_ago = datetime.utcnow() - timedelta(days=1)
            
            # Убираем timestamp из фильтров для сравнения
            compare_filters = {k: v for k, v in filters.items() if k != 'search_timestamp'}

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
                # Убираем timestamp из сохраненных фильтров для сравнения
                session_filters = {k: v for k, v in session.filters.items() if k != 'search_timestamp'}
                if session_filters == compare_filters:
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

    async def _fetch_all_profile_ids(
        self,
        keycloak_id: str,
        search_type: str,
        filters: Dict[str, Any]
    ) -> Tuple[List[str], int]:
        """
        Получает ВСЕ Keycloak ID профилей из profile-service.
        Использует пагинацию через while True для надежного получения всех результатов.
        
        Args:
            keycloak_id: ID текущего пользователя (для исключения)
            search_type: Тип поиска (classic/targeted)
            filters: Фильтры поиска
        
        Returns:
            Tuple[List[str], int]: (список Keycloak ID профилей, общее количество)
        """
        try:
            all_profile_ids = []
            page = 1
            page_size = 100  # Размер страницы для запросов к profile-service
            
            while True:
                # Формируем параметры запроса
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
                    "page": page,
                    "limit": page_size
                }
                
                # Выполняем запрос к profile-service
                result = await self.profile_client.search_profiles(search_params)
                
                if not result:
                    logger.warning(f"No results from profile-service for page {page}")
                    break
                
                profiles_data = result.get("profiles", [])
                
                if not profiles_data:
                    # Нет больше профилей - выходим
                    logger.debug(f"No more profiles at page {page}")
                    break
                
                # Извлекаем Keycloak ID из каждого профиля
                for profile in profiles_data:
                    basic = profile.get("basic", {})
                    profile_keycloak_id = basic.get("keycloak_id") or profile.get("keycloak_id")
                    if profile_keycloak_id:
                        all_profile_ids.append(profile_keycloak_id)
                    else:
                        logger.warning(f"Profile without keycloak_id found: {profile.get('id')}")
                
                logger.debug(f"Fetched page {page}: {len(profiles_data)} profiles, total so far: {len(all_profile_ids)}")
                
                # Условие выхода: получили меньше, чем page_size
                # Это значит, что это последняя страница
                if len(profiles_data) < page_size:
                    logger.info(f"Fetched all profiles: {len(all_profile_ids)} total")
                    break
                
                # Переходим к следующей странице
                page += 1
                
                # Защита от бесконечного цикла (максимум 100 страниц = 10,000 профилей)
                if page > 100:
                    logger.error(f"Too many pages ({page}) while fetching profiles for {keycloak_id[:8]}...")
                    break
            
            return all_profile_ids, len(all_profile_ids)
            
        except Exception as e:
            logger.error(f"Failed to fetch profile IDs for {keycloak_id[:8]}...: {str(e)}", exc_info=True)
            return [], 0

    async def _get_profiles_page_from_ids(
        self,
        all_profile_ids: List[str],
        viewed_profile_ids: List[str],
        page: int,
        limit: int,
        include_detailed: bool
    ) -> Tuple[List[ProfilePreviewResponse], List[str], bool, bool]:
        """
        Получает страницу профилей из списка всех ID, исключая просмотренные
        Возвращает: (профили, ID текущей страницы, has_next, has_previous)
        """
        viewed_set = set(viewed_profile_ids or [])
        available_ids = [pid for pid in all_profile_ids if pid not in viewed_set]
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        if start_idx >= len(available_ids):
            return [], [], False, page > 1
        
        page_ids = available_ids[start_idx:end_idx]
        
        profiles = await self._get_profiles_by_keycloak_ids(page_ids, include_detailed)
        
        has_next = end_idx < len(available_ids)
        has_previous = page > 1
        
        return profiles, page_ids, has_next, has_previous

    async def classic_search(
            self,
            keycloak_id: str,
            search_params: SearchRequest,
            page: int = 1,
            limit: int = 10
    ) -> SearchResponse:
        """Выполняет классический поиск по профилям"""
        if search_params.min_age and search_params.max_age and search_params.min_age > search_params.max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        search_filters = {
            "search_type": "classic",
            "search_timestamp": datetime.utcnow().isoformat(),
            "gender": search_params.gender.value if search_params.gender else None,
            "min_age": search_params.min_age,
            "max_age": search_params.max_age,
            "city": search_params.city
        }

        try:
            existing_session = await self._get_existing_session(keycloak_id, "classic", search_filters)

            if existing_session:
                logger.info(f"Found existing search session {existing_session.id} for user {keycloak_id}")
                
                profiles, page_ids, has_next, has_previous = await self._get_profiles_page_from_ids(
                    all_profile_ids=existing_session.result_profile_ids or [],
                    viewed_profile_ids=existing_session.viewed_profile_ids or [],
                    page=page,
                    limit=limit,
                    include_detailed=False
                )
                
                if page_ids:
                    if existing_session.viewed_profile_ids is None:
                        existing_session.viewed_profile_ids = []
                    existing_session.viewed_profile_ids.extend(page_ids)
                    existing_session.updated_at = datetime.utcnow()
                    await self.db.commit()
                
                total_unviewed = len([pid for pid in (existing_session.result_profile_ids or []) 
                                     if pid not in (existing_session.viewed_profile_ids or [])])
                total_pages = (total_unviewed + limit - 1) // limit if total_unviewed > 0 else 1
                
                pagination = PaginationInfo(
                    current_page=page,
                    total_pages=total_pages,
                    total_results=existing_session.total_results,
                    page_size=limit
                )
                
                return SearchResponse(
                    search_session_id=existing_session.id,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    pagination=pagination,
                    lock_info=None
                )

            all_profile_ids, total = await self._fetch_all_profile_ids(
                keycloak_id=keycloak_id,
                search_type="classic",
                filters=search_filters
            )

            if not all_profile_ids:
                pagination = PaginationInfo(
                    current_page=page,
                    total_pages=1,
                    total_results=0,
                    page_size=limit
                )
                
                search_session = SearchSession(
                    keycloak_id=keycloak_id,
                    search_type='classic',
                    filters=search_filters,
                    result_profile_ids=[],
                    viewed_profile_ids=[],
                    total_results=0
                )
                self.db.add(search_session)
                await self.db.commit()
                await self.db.refresh(search_session)
                
                return SearchResponse(
                    search_session_id=search_session.id,
                    profiles=[],
                    filters=search_filters,
                    created_at=search_session.created_at,
                    pagination=pagination,
                    lock_info=None
                )

            profiles, page_ids, has_next, has_previous = await self._get_profiles_page_from_ids(
                all_profile_ids=all_profile_ids,
                viewed_profile_ids=[],
                page=page,
                limit=limit,
                include_detailed=False
            )

            total_pages = (len(all_profile_ids) + limit - 1) // limit
            search_session = SearchSession(
                keycloak_id=keycloak_id,
                search_type='classic',
                filters=search_filters,
                result_profile_ids=all_profile_ids,
                viewed_profile_ids=page_ids,
                total_results=total
            )
            self.db.add(search_session)
            await self.db.commit()
            await self.db.refresh(search_session)

            pagination = PaginationInfo(
                current_page=page,
                total_pages=total_pages,
                total_results=total,
                page_size=limit
            )

            return SearchResponse(
                search_session_id=search_session.id,
                profiles=profiles,
                filters=search_filters,
                created_at=search_session.created_at,
                pagination=pagination,
                lock_info=None
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
            search_params: TargetedSearchRequest,
            page: int = 1,
            limit: int = 10
    ) -> SearchResponse:
        """Выполняет таргетированный поиск с блокировкой"""
        if search_params.min_age and search_params.max_age and search_params.min_age > search_params.max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        try:
            # Сбрасываем истекшую блокировку если есть
            await self._reset_lock_if_needed(keycloak_id)
            
            # Проверяем блокировку (без обновления счетчика)
            is_locked, unlock_time, total_viewed = await self._check_and_update_lock(
                keycloak_id, new_views=0
            )

            if is_locked:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())
                raise SearchLockedException(
                    message=f"Targeted search is locked. You've viewed {total_viewed} profiles. "
                            f"Next search available in {time_until_unlock // 60} minutes",
                    unlock_time=unlock_time,
                    time_until_unlock=time_until_unlock,
                    profiles_viewed=total_viewed
                )

            search_filters = {
                "search_type": "targeted",
                "search_timestamp": datetime.utcnow().isoformat(),
                "gender": search_params.gender.value if search_params.gender else None,
                "min_age": search_params.min_age,
                "max_age": search_params.max_age,
                "city": search_params.city,
                "education": search_params.education,
                "hobbies_keywords": search_params.hobbies_keywords,
                "partner_preferences": search_params.partner_preferences,
                "online_only": search_params.online_only
            }

            existing_session = await self._get_existing_session(keycloak_id, "targeted", search_filters)

            if existing_session:
                logger.info(f"Found existing targeted session {existing_session.id} for user {keycloak_id}")

                profiles, page_ids, has_next, has_previous = await self._get_profiles_page_from_ids(
                    all_profile_ids=existing_session.result_profile_ids or [],
                    viewed_profile_ids=existing_session.viewed_profile_ids or [],
                    page=page,
                    limit=limit,
                    include_detailed=True
                )
                
                # Обновляем счетчик блокировки с количеством новых просмотров
                if page_ids:
                    if existing_session.viewed_profile_ids is None:
                        existing_session.viewed_profile_ids = []
                    existing_session.viewed_profile_ids.extend(page_ids)
                    existing_session.updated_at = datetime.utcnow()
                    
                    # Атомарно обновляем блокировку
                    is_locked, unlock_time, new_total_viewed = await self._check_and_update_lock(
                        keycloak_id, new_views=len(page_ids)
                    )
                    
                    await self.db.commit()
                else:
                    is_locked, unlock_time, new_total_viewed = await self._check_and_update_lock(
                        keycloak_id, new_views=0
                    )
                
                total_unviewed = len([pid for pid in (existing_session.result_profile_ids or []) 
                                     if pid not in (existing_session.viewed_profile_ids or [])])
                total_pages = (total_unviewed + limit - 1) // limit if total_unviewed > 0 else 1
                
                pagination = PaginationInfo(
                    current_page=page,
                    total_pages=total_pages,
                    total_results=existing_session.total_results,
                    page_size=limit
                )
                
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

            # Получаем все ID профилей за один запрос
            all_profile_ids, total = await self._fetch_all_profile_ids(
                keycloak_id=keycloak_id,
                search_type="targeted",
                filters=search_filters
            )

            if not all_profile_ids:
                pagination = PaginationInfo(
                    current_page=page,
                    total_pages=1,
                    total_results=0,
                    page_size=limit
                )
                
                search_session = SearchSession(
                    keycloak_id=keycloak_id,
                    search_type='targeted',
                    filters=search_filters,
                    result_profile_ids=[],
                    viewed_profile_ids=[],
                    total_results=0
                )
                self.db.add(search_session)
                await self.db.commit()
                await self.db.refresh(search_session)
                
                return SearchResponse(
                    search_session_id=search_session.id,
                    profiles=[],
                    filters=search_filters,
                    created_at=search_session.created_at,
                    pagination=pagination,
                    lock_info=None
                )

            # Получаем первую страницу профилей
            profiles, page_ids, has_next, has_previous = await self._get_profiles_page_from_ids(
                all_profile_ids=all_profile_ids,
                viewed_profile_ids=[],
                page=page,
                limit=limit,
                include_detailed=True
            )

            # Сохраняем сессию
            total_pages = (len(all_profile_ids) + limit - 1) // limit
            search_session = SearchSession(
                keycloak_id=keycloak_id,
                search_type='targeted',
                filters=search_filters,
                result_profile_ids=all_profile_ids,
                viewed_profile_ids=page_ids,
                total_results=total
            )
            self.db.add(search_session)
            
            # Атомарно обновляем блокировку с количеством новых просмотров
            is_locked, unlock_time, new_total_viewed = await self._check_and_update_lock(
                keycloak_id, new_views=len(page_ids)
            )
            
            await self.db.commit()
            await self.db.refresh(search_session)

            pagination = PaginationInfo(
                current_page=page,
                total_pages=total_pages,
                total_results=total,
                page_size=limit
            )
            
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
                profiles=profiles,
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

    async def get_search_lock_status(self, keycloak_id: str) -> SearchLockInfo:
        """Получает статус блокировки поиска для пользователя"""
        try:
            # Сначала сбрасываем истекшую блокировку если есть
            await self._reset_lock_if_needed(keycloak_id)
            
            # Получаем актуальное состояние
            is_locked, unlock_time, total_viewed = await self._check_and_update_lock(
                keycloak_id, new_views=0
            )

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

    async def get_search_session(self, session_id: int, keycloak_id: str) -> SearchSessionInfo:
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