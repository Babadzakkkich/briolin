from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database.models import SearchSession
from app.schemas.search import (
    SearchRequest,
    TargetedSearchRequest,
    SearchResponse,
    SearchSessionResponse,
    ProfilePreviewResponse,
    SearchLockInfoResponse
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
        """
        Инициализация сервиса
        :param db: Сессия для своей БД (search_sessions)
        :param profile_client: Клиент для profile-service
        """
        self.db = db
        self.profile_client = profile_client

    async def _check_targeted_search_lock(self, user_id: int) -> Tuple[
        bool, Optional[datetime], int, Optional[SearchSession]]:
        """
        Проверяет, заблокирован ли таргетированный поиск для пользователя
        Возвращает: (заблокирован, время разблокировки, количество просмотренных профилей, последняя сессия)
        """
        try:
            # Ищем все сессии таргетированного поиска за последние N часов
            lock_period = datetime.utcnow() - timedelta(hours=settings.targeted_search_lock_hours)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.user_id == user_id,
                    SearchSession.search_type == 'targeted',
                    SearchSession.created_at >= lock_period
                )
            ).order_by(SearchSession.created_at.desc())

            result = await self.db.execute(stmt)
            recent_sessions = result.scalars().all()

            if not recent_sessions:
                return False, None, 0, None

            # Суммируем просмотренные профили за последние N часов
            total_viewed = 0
            for session in recent_sessions:
                if session.viewed_profiles:
                    total_viewed += len(session.viewed_profiles)

            # Получаем последнюю сессию
            last_session = recent_sessions[0] if recent_sessions else None

            # Если просмотрено >= лимита - блокировка
            if total_viewed >= settings.profiles_per_page:
                # Самая старая сессия в этом периоде
                first_session = recent_sessions[-1]
                unlock_time = first_session.created_at + timedelta(hours=settings.targeted_search_lock_hours)

                if unlock_time > datetime.utcnow():
                    return True, unlock_time, total_viewed, last_session

            return False, None, total_viewed, last_session

        except Exception as e:
            logger.error(f"Error checking search lock for user {user_id}: {str(e)}")
            return False, None, 0, None

    async def _get_existing_session(
            self,
            user_id: int,
            search_type: str,
            filters: Dict[str, Any]
    ) -> Optional[SearchSession]:
        """Проверяет, существует ли активная сессия с такими же фильтрами"""
        try:
            # Ищем сессию с такими же фильтрами, созданную за последние 24 часа
            day_ago = datetime.utcnow() - timedelta(days=1)

            # Получаем все сессии пользователя за последние 24 часа
            stmt = select(SearchSession).where(
                and_(
                    SearchSession.user_id == user_id,
                    SearchSession.search_type == search_type,
                    SearchSession.created_at >= day_ago
                )
            ).order_by(SearchSession.created_at.desc())

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            # Сравниваем фильтры
            for session in sessions:
                if session.filters == filters:
                    return session

            return None

        except Exception as e:
            logger.error(f"Error checking existing session: {str(e)}")
            return None

    async def _get_profiles_by_ids(
            self,
            profile_ids: List[int],
            include_detailed: bool = False
    ) -> List[ProfilePreviewResponse]:
        """
        Получает детальную информацию о профилях по их ID через profile-service
        """
        if not profile_ids:
            return []

        try:
            # Получаем профили через клиент
            profiles_data = await self.profile_client.get_profiles_batch(profile_ids)

            result_profiles = []
            for profile in profiles_data:
                # Извлекаем данные из ответа profile-service
                basic = profile.get("basic", {})
                detailed = profile.get("detailed")

                # Рассчитываем возраст
                birth_date_str = basic.get("date_of_birth")
                age = 0
                if birth_date_str:
                    try:
                        birth_date = datetime.fromisoformat(birth_date_str).date()
                        age = calculate_age_from_birth_date(birth_date)
                    except:
                        pass

                result_profiles.append(ProfilePreviewResponse(
                    first_name=basic.get("first_name", ""),
                    last_name=basic.get("last_name", ""),
                    gender=basic.get("gender", ""),
                    age=age,
                    city=basic.get("city", ""),
                    online=basic.get("online", False),
                    education=detailed.get("education") if detailed else None,
                    hobbies=detailed.get("hobbies") if detailed else None,
                    about_me=detailed.get("about_me") if detailed else None,
                    partner_preferences=detailed.get("partner_preferences") if detailed else None
                ))

            return result_profiles

        except Exception as e:
            logger.error(f"Error getting profiles by ids: {str(e)}")
            return []

    async def _perform_search(
            self,
            user_id: int,
            keycloak_id: str,
            search_type: str,
            filters: Dict[str, Any]
    ) -> Tuple[List[ProfilePreviewResponse], List[int], int, int]:
        """
        Выполняет поиск через profile-service
        Возвращает: (профили, ID профилей, общее количество, количество страниц)
        """
        try:
            # Подготавливаем параметры для profile-service
            search_params = {
                "gender": filters.get("gender"),
                "min_age": filters.get("min_age"),
                "max_age": filters.get("max_age"),
                "city": filters.get("city"),
                "education": filters.get("education"),
                "hobbies_keywords": filters.get("hobbies_keywords"),
                "partner_preferences": filters.get("partner_preferences"),
                "online_only": filters.get("online_only", False),
                "exclude_keycloak_id": keycloak_id,  # Исключаем текущего пользователя
                "page": filters.get("page", 1),
                "limit": filters.get("limit", 10)
            }

            # Выполняем поиск через profile-service
            result = await self.profile_client.search_profiles(search_params)

            if not result:
                return [], [], 0, 1

            profiles_data = result.get("profiles", [])
            total = result.get("total", 0)
            total_pages = result.get("total_pages", 1)

            # Конвертируем в ProfilePreviewResponse и собираем ID
            profiles = []
            profile_ids = []
            
            for profile in profiles_data:
                basic = profile.get("basic", {})
                detailed = profile.get("detailed")

                # Получаем ID профиля
                profile_id = basic.get("id") or profile.get("id")
                if profile_id:
                    profile_ids.append(profile_id)

                # Рассчитываем возраст
                birth_date_str = basic.get("date_of_birth")
                age = 0
                if birth_date_str:
                    try:
                        birth_date = datetime.fromisoformat(birth_date_str).date()
                        age = calculate_age_from_birth_date(birth_date)
                    except:
                        pass

                profiles.append(ProfilePreviewResponse(
                    first_name=basic.get("first_name", ""),
                    last_name=basic.get("last_name", ""),
                    gender=basic.get("gender", ""),
                    age=age,
                    city=basic.get("city", ""),
                    online=basic.get("online", False),
                    education=detailed.get("education") if detailed else None,
                    hobbies=detailed.get("hobbies") if detailed else None,
                    about_me=detailed.get("about_me") if detailed else None,
                    partner_preferences=detailed.get("partner_preferences") if detailed else None
                ))

            return profiles, profile_ids, total, total_pages

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], [], 0, 1

    async def _get_profiles_page_from_session(
            self,
            session: SearchSession,
            page: int,
            limit: int
    ) -> Tuple[List[ProfilePreviewResponse], bool, bool]:
        """
        Получает страницу профилей из существующей сессии
        Возвращает: (профили, has_next, has_previous)
        """
        all_results = session.results or []
        viewed = session.viewed_profiles or []
        
        # Получаем ID непросмотренных профилей
        available_ids = [pid for pid in all_results if pid not in viewed]
        
        # Пагинация
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        if start_idx >= len(available_ids):
            return [], False, page > 1
        
        page_ids = available_ids[start_idx:end_idx]
        
        # Получаем профили по ID
        profiles = await self._get_profiles_by_ids(page_ids, include_detailed=(session.search_type == 'targeted'))
        
        # Обновляем просмотренные
        session.viewed_profiles = viewed + page_ids
        session.current_page = page
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        
        has_next = end_idx < len(available_ids)
        has_previous = page > 1
        
        return profiles, has_next, has_previous

    async def classic_search(
            self,
            user_id: int,
            keycloak_id: str,
            gender: Optional[str] = None,
            min_age: Optional[int] = None,
            max_age: Optional[int] = None,
            city: Optional[str] = None,
            page: int = 1,
            limit: int = 10
    ) -> SearchResponse:
        """
        Выполняет классический поиск по профилям
        """
        # Валидация параметров
        if min_age and max_age and min_age > max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        # Формируем фильтры
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
            # Проверяем существующую сессию
            existing_session = await self._get_existing_session(user_id, "classic", search_filters)

            if existing_session:
                logger.info(f"Found existing search session {existing_session.id} for user {user_id}")
                
                # Получаем страницу из существующей сессии
                profiles, has_next, has_previous = await self._get_profiles_page_from_session(
                    existing_session, page, limit
                )
                
                return SearchResponse(
                    search_session_id=existing_session.id,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    current_page=page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    has_next=has_next,
                    has_previous=has_previous
                )

            # Выполняем новый поиск
            profiles, profile_ids, total, total_pages = await self._perform_search(
                user_id=user_id,
                keycloak_id=keycloak_id,
                search_type="classic",
                filters=search_filters
            )

            # Пагинация для первой страницы
            start_idx = 0
            end_idx = min(limit, len(profile_ids))
            first_page_ids = profile_ids[start_idx:end_idx]
            
            # Получаем профили для первой страницы
            first_page_profiles = await self._get_profiles_by_ids(first_page_ids, include_detailed=False)

            # Сохраняем сессию
            search_session = SearchSession(
                user_id=user_id,
                keycloak_id=keycloak_id,
                search_type='classic',
                filters=search_filters,
                results=profile_ids,
                viewed_profiles=first_page_ids,  # Отмечаем первую страницу как просмотренную
                current_page=page,
                total_pages=total_pages,
                total_results=total,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(search_session)
            await self.db.commit()
            await self.db.refresh(search_session)

            has_next = (page * limit) < total
            has_previous = page > 1

            return SearchResponse(
                search_session_id=search_session.id,
                profiles=first_page_profiles,
                filters=search_filters,
                created_at=search_session.created_at,
                current_page=page,
                total_pages=total_pages,
                total_results=total,
                has_next=has_next,
                has_previous=has_previous
            )

        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Search failed for user {user_id}: {str(e)}")
            raise DatabaseException(f"Search failed: {str(e)}")

    async def targeted_search(
            self,
            user_id: int,
            keycloak_id: str,
            search_params: TargetedSearchRequest
    ) -> SearchResponse:
        """
        Выполняет таргетированный поиск с блокировкой
        """
        if search_params.min_age and search_params.max_age and search_params.min_age > search_params.max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        try:
            # Проверяем блокировку
            is_locked, unlock_time, total_viewed, last_session = await self._check_targeted_search_lock(user_id)

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
            existing_session = await self._get_existing_session(user_id, "targeted", search_filters)

            if existing_session:
                logger.info(f"Found existing targeted session {existing_session.id} for user {user_id}")

                # Получаем страницу из существующей сессии
                profiles, has_next, has_previous = await self._get_profiles_page_from_session(
                    existing_session, search_params.page, search_params.limit
                )
                
                # Проверяем блокировку после обновления
                is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(user_id)
                
                response = SearchResponse(
                    search_session_id=existing_session.id,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    current_page=search_params.page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    has_next=has_next,
                    has_previous=has_previous,
                    profiles_viewed=new_total_viewed
                )
                
                if is_locked:
                    response.locked_until = unlock_time
                    response.time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())
                
                return response

            # Выполняем новый поиск
            profiles, profile_ids, total, total_pages = await self._perform_search(
                user_id=user_id,
                keycloak_id=keycloak_id,
                search_type="targeted",
                filters=search_filters
            )

            # Пагинация для первой страницы
            start_idx = 0
            end_idx = min(search_params.limit, len(profile_ids))
            first_page_ids = profile_ids[start_idx:end_idx]
            
            # Получаем профили для первой страницы
            first_page_profiles = await self._get_profiles_by_ids(first_page_ids, include_detailed=True)

            # Сохраняем сессию
            search_session = SearchSession(
                user_id=user_id,
                keycloak_id=keycloak_id,
                search_type='targeted',
                filters=search_filters,
                results=profile_ids,
                viewed_profiles=first_page_ids,  # Отмечаем первую страницу как просмотренную
                current_page=search_params.page,
                total_pages=total_pages,
                total_results=total,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(search_session)
            await self.db.commit()
            await self.db.refresh(search_session)

            # Проверяем блокировку
            is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(user_id)

            has_next = (search_params.page * search_params.limit) < total
            has_previous = search_params.page > 1

            response = SearchResponse(
                search_session_id=search_session.id,
                profiles=first_page_profiles,
                filters=search_filters,
                created_at=search_session.created_at,
                current_page=search_params.page,
                total_pages=total_pages,
                total_results=total,
                has_next=has_next,
                has_previous=has_previous,
                profiles_viewed=new_total_viewed
            )

            if is_locked:
                response.locked_until = unlock_time
                response.time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())

            return response

        except SearchLockedException:
            raise
        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Targeted search failed for user {user_id}: {str(e)}")
            raise DatabaseException(f"Targeted search failed: {str(e)}")

    async def get_search_lock_status(self, user_id: int) -> SearchLockInfoResponse:
        """Получает статус блокировки поиска для пользователя"""
        try:
            is_locked, unlock_time, total_viewed, _ = await self._check_targeted_search_lock(user_id)

            time_until_unlock = None
            if unlock_time:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())

            return SearchLockInfoResponse(
                search_type='targeted',
                is_locked=is_locked,
                profiles_viewed=total_viewed,
                locked_until=unlock_time,
                time_until_unlock=time_until_unlock
            )

        except Exception as e:
            logger.error(f"Failed to get search lock status for user {user_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search lock status: {str(e)}")

    async def get_search_history(
            self,
            user_id: int,
            limit: int = 50,
            search_type: Optional[str] = None
    ) -> List[SearchSessionResponse]:
        """Получение истории поисковых сессий пользователя"""
        try:
            stmt = select(SearchSession).where(SearchSession.user_id == user_id)

            if search_type:
                stmt = stmt.where(SearchSession.search_type == search_type)

            stmt = stmt.order_by(SearchSession.created_at.desc()).limit(limit)

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            return [
                SearchSessionResponse(
                    search_session_id=session.id,
                    search_type=session.search_type,
                    filters=session.filters,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    total_results=session.total_results,
                    current_page=session.current_page,
                    total_pages=session.total_pages,
                    user_id=session.user_id
                )
                for session in sessions
            ]
        except Exception as e:
            logger.error(f"Failed to get search history for user {user_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search history: {str(e)}")

    async def get_search_session(self, session_id: int) -> SearchSessionResponse:
        """Получение конкретной поисковой сессии"""
        try:
            stmt = select(SearchSession).where(SearchSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                raise SearchSessionNotFoundException(f"Search session {session_id} not found")

            return SearchSessionResponse(
                search_session_id=session.id,
                search_type=session.search_type,
                filters=session.filters,
                created_at=session.created_at,
                updated_at=session.updated_at,
                total_results=session.total_results,
                current_page=session.current_page,
                total_pages=session.total_pages,
                user_id=session.user_id
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

    async def delete_search_history(self, user_id: int, older_than_days: int = 30) -> int:
        """Удаление старой истории поиска"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.user_id == user_id,
                    SearchSession.created_at < cutoff_date
                )
            )

            result = await self.db.execute(stmt)
            sessions = result.scalars().all()

            for session in sessions:
                await self.db.delete(session)

            await self.db.commit()

            deleted_count = len(sessions)
            logger.info(f"Deleted {deleted_count} old search sessions for user {user_id}")

            return deleted_count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete search history for user {user_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete search history: {str(e)}")