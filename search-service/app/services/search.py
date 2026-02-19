from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.database.models import BasicProfile, DetailedProfile, SearchSession
from app.schemas.search import (
    SearchRequest,
    TargetedSearchRequest,
    SearchResponse,
    SearchSessionResponse,
    ProfilePreviewResponse,
    SearchLockInfoResponse
)
from app.core.logger import logger
from app.core.exceptions import (
    DatabaseException,
    SearchSessionNotFoundException,
    InvalidSearchParametersException,
    SearchLockedException
)
from app.utils.age_calculator import calculate_age


class SearchService:
    # Константы
    TARGETED_SEARCH_LOCK_HOURS = 12  # Блокировка на 12 часов
    PROFILES_PER_PAGE = 10  # Профилей на странице

    def __init__(self, own_db: AsyncSession, profile_db: AsyncSession):
        """
        Инициализация сервиса с двумя сессиями БД
        :param own_db: Сессия для своей БД (search_sessions)
        :param profile_db: Сессия для БД profile-service (только чтение)
        """
        self.own_db = own_db
        self.profile_db = profile_db

    async def _check_targeted_search_lock(self, user_id: int) -> Tuple[
        bool, Optional[datetime], int, Optional[SearchSession]]:
        """
        Проверяет, заблокирован ли таргетированный поиск для пользователя
        Возвращает: (заблокирован, время разблокировки, количество просмотренных профилей, последняя сессия)
        """
        try:
            # Ищем все сессии таргетированного поиска за последние 12 часов
            lock_period = datetime.utcnow() - timedelta(hours=self.TARGETED_SEARCH_LOCK_HOURS)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.user_id == user_id,
                    SearchSession.search_type == 'targeted',
                    SearchSession.created_at >= lock_period
                )
            ).order_by(SearchSession.created_at.desc())

            result = await self.own_db.execute(stmt)
            recent_sessions = result.scalars().all()

            if not recent_sessions:
                return False, None, 0, None

            # Суммируем просмотренные профили за последние 12 часов
            total_viewed = 0
            for session in recent_sessions:
                if session.viewed_profiles:
                    total_viewed += len(session.viewed_profiles)

            # Получаем последнюю сессию
            last_session = recent_sessions[0] if recent_sessions else None

            # Если просмотрено >= 10 профилей - блокировка
            if total_viewed >= self.PROFILES_PER_PAGE:
                # Самая старая сессия в этом периоде
                first_session = recent_sessions[-1]
                unlock_time = first_session.created_at + timedelta(hours=self.TARGETED_SEARCH_LOCK_HOURS)

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

            result = await self.own_db.execute(stmt)
            sessions = result.scalars().all()

            # Сравниваем фильтры на Python стороне (безопасно)
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
        """Получает детальную информацию о профилях по их ID"""
        if not profile_ids:
            return []

        try:
            if include_detailed:
                # Получаем BasicProfile и DetailedProfile отдельными запросами
                # и связываем их в коде

                # 1. Получаем BasicProfile
                basic_stmt = select(BasicProfile).where(BasicProfile.id.in_(profile_ids))
                basic_result = await self.profile_db.execute(basic_stmt)
                basic_profiles = basic_result.scalars().all()

                # 2. Получаем DetailedProfile отдельным запросом
                detailed_stmt = select(DetailedProfile).where(
                    DetailedProfile.basic_profile_id.in_(profile_ids)
                )
                detailed_result = await self.profile_db.execute(detailed_stmt)
                detailed_profiles = {dp.basic_profile_id: dp for dp in detailed_result.scalars().all()}

                # 3. Связываем в коде
                result_profiles = []
                for profile in basic_profiles:
                    age = calculate_age(profile.date_of_birth)
                    detailed = detailed_profiles.get(profile.id)

                    result_profiles.append(ProfilePreviewResponse(
                        user_id=profile.id,
                        keycloak_id=profile.keycloak_id,
                        first_name=profile.first_name,
                        last_name=profile.last_name,
                        gender=profile.gender,
                        age=age,
                        city=profile.city,
                        online=profile.online,
                        last_login_at=profile.last_login_at,
                        education=detailed.education if detailed else None,
                        hobbies=detailed.hobbies if detailed else None,
                        about_me=detailed.about_me if detailed else None,
                        partner_preferences=detailed.partner_preferences if detailed else None
                    ))
                return result_profiles
            else:
                # Только basic_profiles
                stmt = select(BasicProfile).where(BasicProfile.id.in_(profile_ids))
                result = await self.profile_db.execute(stmt)
                profiles = result.scalars().all()

                result_profiles = []
                for profile in profiles:
                    age = calculate_age(profile.date_of_birth)
                    result_profiles.append(ProfilePreviewResponse(
                        user_id=profile.id,
                        keycloak_id=profile.keycloak_id,
                        first_name=profile.first_name,
                        last_name=profile.last_name,
                        gender=profile.gender,
                        age=age,
                        city=profile.city,
                        online=profile.online,
                        last_login_at=profile.last_login_at
                    ))
                return result_profiles

        except Exception as e:
            logger.error(f"Error getting profiles by ids: {str(e)}")
            return []

    async def _build_classic_search_query(
            self,
            user_id: int,
            gender: Optional[str] = None,
            min_age: Optional[int] = None,
            max_age: Optional[int] = None,
            city: Optional[str] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Строит ORM запрос для классического поиска
        """
        # Базовый запрос
        query = select(BasicProfile)

        # Условия фильтрации
        conditions = [BasicProfile.id != user_id]  # Исключаем текущего пользователя

        if gender:
            conditions.append(BasicProfile.gender == gender)

        if city:
            conditions.append(BasicProfile.city == city)

        # Возрастная фильтрация через SQL выражение
        if min_age is not None:
            conditions.append(
                func.extract('year', func.age(BasicProfile.date_of_birth)) >= min_age
            )

        if max_age is not None:
            conditions.append(
                func.extract('year', func.age(BasicProfile.date_of_birth)) <= max_age
            )

        # Применяем все условия
        query = query.where(and_(*conditions))

        return query, {}

    async def _build_targeted_search_query(
            self,
            user_id: int,
            params: TargetedSearchRequest
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Строит ORM запрос для таргетированного поиска с фильтрацией по detailed_profiles
        """
        # Используем явный JOIN
        query = select(BasicProfile).join(
            DetailedProfile,
            BasicProfile.id == DetailedProfile.basic_profile_id,
            isouter=True  # LEFT JOIN чтобы включить профили без detailed
        )

        # Условия фильтрации
        conditions = [BasicProfile.id != user_id]  # Исключаем текущего пользователя

        # Фильтры из basic_profiles
        if params.gender:
            conditions.append(BasicProfile.gender == params.gender)

        if params.city:
            conditions.append(BasicProfile.city == params.city)

        if params.online_only:
            conditions.append(BasicProfile.online == True)

        # Возрастная фильтрация
        if params.min_age is not None:
            conditions.append(
                func.extract('year', func.age(BasicProfile.date_of_birth)) >= params.min_age
            )

        if params.max_age is not None:
            conditions.append(
                func.extract('year', func.age(BasicProfile.date_of_birth)) <= params.max_age
            )

        # Фильтры из detailed_profiles (только если указаны и не пустые)
        detailed_conditions = []

        if params.education and params.education.strip():
            detailed_conditions.append(
                DetailedProfile.education.ilike(f"%{params.education.strip()}%")
            )

        if params.partner_preferences and params.partner_preferences.strip():
            detailed_conditions.append(
                DetailedProfile.partner_preferences.ilike(f"%{params.partner_preferences.strip()}%")
            )

        if params.hobbies_keywords:
            # Фильтруем пустые ключевые слова
            valid_keywords = [kw.strip() for kw in params.hobbies_keywords if kw and kw.strip()]
            if valid_keywords:
                hobby_conditions = []
                for keyword in valid_keywords:
                    hobby_conditions.append(
                        DetailedProfile.hobbies.ilike(f"%{keyword}%")
                    )
                if hobby_conditions:
                    detailed_conditions.append(or_(*hobby_conditions))

        # Добавляем условия для detailed_profiles, если они есть
        if detailed_conditions:
            conditions.append(and_(*detailed_conditions))

        # Применяем все условия
        query = query.where(and_(*conditions))

        return query, {}

    async def _get_paginated_results(
            self,
            query: Any,
            page: int,
            limit: int,
            include_detailed: bool = False
    ) -> Tuple[List[BasicProfile], int, int]:
        """
        Получает пагинированные результаты и общее количество
        """
        try:
            # Получаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.profile_db.execute(count_query)
            total_results = count_result.scalar() or 0

            # Добавляем сортировку и пагинацию
            paginated_query = query.order_by(
                BasicProfile.last_login_at.desc().nullslast(),
                BasicProfile.id
            ).offset((page - 1) * limit).limit(limit)

            result = await self.profile_db.execute(paginated_query)
            profiles = result.scalars().all()

            return profiles, total_results, (total_results + limit - 1) // limit if total_results > 0 else 1

        except Exception as e:
            logger.error(f"Error in pagination: {str(e)}")
            raise

    async def _convert_profiles_to_response(
            self,
            profiles: List[BasicProfile],
            include_detailed: bool = False
    ) -> Tuple[List[int], List[ProfilePreviewResponse]]:
        """
        Конвертирует ORM объекты в Pydantic модели
        """
        profile_ids = []
        profile_responses = []

        if include_detailed:
            # Если нужны детальные профили, получаем их одним запросом
            detailed_stmt = select(DetailedProfile).where(
                DetailedProfile.basic_profile_id.in_([p.id for p in profiles])
            )
            detailed_result = await self.profile_db.execute(detailed_stmt)
            detailed_map = {dp.basic_profile_id: dp for dp in detailed_result.scalars().all()}

            for profile in profiles:
                profile_ids.append(profile.id)
                age = calculate_age(profile.date_of_birth)
                detailed = detailed_map.get(profile.id)

                profile_responses.append(ProfilePreviewResponse(
                    user_id=profile.id,
                    keycloak_id=profile.keycloak_id,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    gender=profile.gender,
                    age=age,
                    city=profile.city,
                    online=profile.online,
                    last_login_at=profile.last_login_at,
                    education=detailed.education if detailed else None,
                    hobbies=detailed.hobbies if detailed else None,
                    about_me=detailed.about_me if detailed else None,
                    partner_preferences=detailed.partner_preferences if detailed else None
                ))
        else:
            for profile in profiles:
                profile_ids.append(profile.id)
                age = calculate_age(profile.date_of_birth)
                profile_responses.append(ProfilePreviewResponse(
                    user_id=profile.id,
                    keycloak_id=profile.keycloak_id,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    gender=profile.gender,
                    age=age,
                    city=profile.city,
                    online=profile.online,
                    last_login_at=profile.last_login_at
                ))

        return profile_ids, profile_responses

    async def _get_next_page_profiles(
            self,
            session: SearchSession,
            page: int,
            limit: int
    ) -> Tuple[List[int], List[ProfilePreviewResponse], bool, bool]:
        """Получает следующую страницу непоказанных профилей"""
        all_results = session.results or []
        viewed = session.viewed_profiles or []

        # Профили, которые еще не показывали
        available_profiles = [pid for pid in all_results if pid not in viewed]

        # Пагинация
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        if start_idx >= len(available_profiles):
            return [], [], False, page > 1

        page_profile_ids = available_profiles[start_idx:end_idx]

        # Получаем детальную информацию
        include_detailed = (session.search_type == 'targeted')
        profiles = await self._get_profiles_by_ids(page_profile_ids, include_detailed)

        has_next = end_idx < len(available_profiles)
        has_previous = page > 1

        return page_profile_ids, profiles, has_next, has_previous

    async def classic_search(
            self,
            user_id: int,
            gender: Optional[str] = None,
            min_age: Optional[int] = None,
            max_age: Optional[int] = None,
            city: Optional[str] = None,
            page: int = 1,
            limit: int = 10
    ) -> SearchResponse:
        """
        Выполняет классический поиск по basic_profiles с пагинацией
        Пустые значения параметров означают "без фильтра"
        """
        # Валидация параметров
        if min_age and max_age and min_age > max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        # Формируем фильтры для сохранения (только непустые значения)
        search_filters = {
            "search_type": "classic",
            "search_timestamp": datetime.utcnow().isoformat()
        }

        # Добавляем только непустые фильтры
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
            # Проверяем, есть ли уже сессия с такими фильтрами
            existing_session = await self._get_existing_session(user_id, "classic", search_filters)

            if existing_session:
                logger.info(f"Found existing search session {existing_session.id} for user {user_id}")

                # Получаем следующую страницу
                page_profile_ids, profiles, has_next, has_previous = await self._get_next_page_profiles(
                    existing_session,
                    page,
                    limit
                )

                if not page_profile_ids and page > 1:
                    # Если запрошенная страница пуста, возвращаем последнюю доступную
                    last_page = existing_session.total_pages
                    if last_page > 0:
                        page_profile_ids, profiles, has_next, has_previous = await self._get_next_page_profiles(
                            existing_session,
                            last_page,
                            limit
                        )
                        page = last_page

                if page_profile_ids:
                    # Обновляем просмотренные профили
                    current_viewed = existing_session.viewed_profiles or []
                    existing_session.viewed_profiles = current_viewed + page_profile_ids
                    existing_session.current_page = page
                    existing_session.updated_at = datetime.utcnow()
                    await self.own_db.commit()

                return SearchResponse(
                    search_session_id=existing_session.id,
                    user_ids=page_profile_ids,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    current_page=page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    has_next=has_next,
                    has_previous=has_previous
                )

            # Если нет существующей сессии - выполняем новый поиск
            # Строим ORM запрос
            query, _ = await self._build_classic_search_query(
                user_id=user_id,
                gender=gender,
                min_age=min_age,
                max_age=max_age,
                city=city
            )

            # Получаем все ID для сохранения (без пагинации)
            all_ids_query = select(BasicProfile.id).where(query.whereclause)
            all_ids_result = await self.profile_db.execute(all_ids_query)
            all_ids = [row[0] for row in all_ids_result.all()]

            # Получаем пагинированные результаты
            profiles_page, total_results, total_pages = await self._get_paginated_results(
                query, page, limit, include_detailed=False
            )

            # Конвертируем в ответ
            page_profile_ids, profile_responses = await self._convert_profiles_to_response(
                profiles_page, include_detailed=False
            )

            # Сохраняем сессию
            search_session = SearchSession(
                user_id=user_id,
                search_type='classic',
                filters=search_filters,
                results=all_ids,
                viewed_profiles=page_profile_ids,
                current_page=page,
                total_pages=total_pages,
                total_results=total_results,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.own_db.add(search_session)
            await self.own_db.commit()
            await self.own_db.refresh(search_session)

            logger.info(f"Classic search completed for user {user_id}, found {total_results} profiles")

            return SearchResponse(
                search_session_id=search_session.id,
                user_ids=page_profile_ids,
                profiles=profile_responses,
                filters=search_filters,
                created_at=search_session.created_at,
                current_page=page,
                total_pages=total_pages,
                total_results=total_results,
                has_next=(page * limit) < total_results,
                has_previous=page > 1
            )

        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.own_db.rollback()
            logger.error(f"Search failed for user {user_id}: {str(e)}")
            raise DatabaseException(f"Search failed: {str(e)}")

    async def targeted_search(
            self,
            user_id: int,
            search_params: TargetedSearchRequest
    ) -> SearchResponse:
        """
        Выполняет таргетированный поиск с блокировкой на 12 часов после 10 просмотренных профилей
        Пустые значения параметров означают "без фильтра"
        """

        # Валидация параметров
        if search_params.min_age and search_params.max_age and search_params.min_age > search_params.max_age:
            raise InvalidSearchParametersException("min_age cannot be greater than max_age")

        try:
            # Проверяем блокировку
            is_locked, unlock_time, total_viewed, last_session = await self._check_targeted_search_lock(user_id)

            if is_locked:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())
                hours = time_until_unlock // 3600
                minutes = (time_until_unlock % 3600) // 60

                raise SearchLockedException(
                    message=f"Targeted search is locked. You've viewed {total_viewed} profiles. "
                            f"Next search available in {hours} hours {minutes} minutes",
                    unlock_time=unlock_time,
                    time_until_unlock=time_until_unlock,
                    profiles_viewed=total_viewed
                )

            # Формируем фильтры для сохранения (только непустые значения)
            search_filters = {
                "search_type": "targeted",
                "search_timestamp": datetime.utcnow().isoformat()
            }

            # Добавляем только непустые параметры
            params_dict = search_params.model_dump(exclude_none=True)
            for key, value in params_dict.items():
                if key not in ['page', 'limit']:  # Исключаем параметры пагинации
                    if isinstance(value, list):
                        if value:  # Непустой список
                            search_filters[key] = value
                    elif value is not None and value != "":
                        search_filters[key] = value

            search_filters["page"] = search_params.page
            search_filters["limit"] = search_params.limit

            # Проверяем, есть ли уже сессия с такими фильтрами
            existing_session = await self._get_existing_session(user_id, "targeted", search_filters)

            if existing_session:
                logger.info(f"Found existing targeted session {existing_session.id} for user {user_id}")

                # Получаем следующую страницу
                page_profile_ids, profiles, has_next, has_previous = await self._get_next_page_profiles(
                    existing_session,
                    search_params.page,
                    search_params.limit
                )

                if not page_profile_ids and search_params.page > 1:
                    # Если запрошенная страница пуста, возвращаем последнюю доступную
                    last_page = existing_session.total_pages
                    if last_page > 0:
                        page_profile_ids, profiles, has_next, has_previous = await self._get_next_page_profiles(
                            existing_session,
                            last_page,
                            search_params.limit
                        )
                        search_params.page = last_page

                if page_profile_ids:
                    # Обновляем просмотренные профили
                    current_viewed = existing_session.viewed_profiles or []
                    existing_session.viewed_profiles = current_viewed + page_profile_ids
                    existing_session.current_page = search_params.page
                    existing_session.updated_at = datetime.utcnow()
                    await self.own_db.commit()

                    # Проверяем блокировку после обновления
                    is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(user_id)

                    if is_locked:
                        time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())

                        return SearchResponse(
                            search_session_id=existing_session.id,
                            user_ids=page_profile_ids,
                            profiles=profiles,
                            filters=search_filters,
                            created_at=existing_session.created_at,
                            current_page=search_params.page,
                            total_pages=existing_session.total_pages,
                            total_results=existing_session.total_results,
                            has_next=False,
                            has_previous=has_previous,
                            locked_until=unlock_time,
                            time_until_unlock=time_until_unlock,
                            profiles_viewed=new_total_viewed
                        )

                return SearchResponse(
                    search_session_id=existing_session.id,
                    user_ids=page_profile_ids,
                    profiles=profiles,
                    filters=search_filters,
                    created_at=existing_session.created_at,
                    current_page=search_params.page,
                    total_pages=existing_session.total_pages,
                    total_results=existing_session.total_results,
                    has_next=has_next,
                    has_previous=has_previous,
                    profiles_viewed=total_viewed + len(page_profile_ids) if page_profile_ids else total_viewed
                )

            # Если нет существующей сессии - выполняем новый поиск
            # Строим ORM запрос
            query, _ = await self._build_targeted_search_query(user_id, search_params)

            # Получаем все ID для сохранения (без пагинации)
            all_ids_query = select(BasicProfile.id).where(query.whereclause)
            all_ids_result = await self.profile_db.execute(all_ids_query)
            all_ids = [row[0] for row in all_ids_result.all()]

            # Получаем пагинированные результаты
            profiles_page, total_results, total_pages = await self._get_paginated_results(
                query, search_params.page, search_params.limit, include_detailed=True
            )

            # Конвертируем в ответ
            page_profile_ids, profile_responses = await self._convert_profiles_to_response(
                profiles_page, include_detailed=True
            )

            # Сохраняем сессию
            search_session = SearchSession(
                user_id=user_id,
                search_type='targeted',
                filters=search_filters,
                results=all_ids,
                viewed_profiles=page_profile_ids,
                current_page=search_params.page,
                total_pages=total_pages,
                total_results=total_results,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.own_db.add(search_session)
            await self.own_db.commit()
            await self.own_db.refresh(search_session)

            # Проверяем, не достигли ли лимита
            is_locked, unlock_time, new_total_viewed, _ = await self._check_targeted_search_lock(user_id)

            logger.info(f"Targeted search completed for user {user_id}, found {total_results} profiles")

            response = SearchResponse(
                search_session_id=search_session.id,
                user_ids=page_profile_ids,
                profiles=profile_responses,
                filters=search_filters,
                created_at=search_session.created_at,
                current_page=search_params.page,
                total_pages=total_pages,
                total_results=total_results,
                has_next=(search_params.page * search_params.limit) < total_results,
                has_previous=search_params.page > 1,
                profiles_viewed=len(page_profile_ids)
            )

            if is_locked:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())
                response.locked_until = unlock_time
                response.time_until_unlock = time_until_unlock

            return response

        except SearchLockedException:
            raise
        except InvalidSearchParametersException:
            raise
        except Exception as e:
            await self.own_db.rollback()
            logger.error(f"Targeted search failed for user {user_id}: {str(e)}")
            raise DatabaseException(f"Targeted search failed: {str(e)}")

    async def get_search_lock_status(self, user_id: int) -> SearchLockInfoResponse:
        """Получает статус блокировки поиска для пользователя"""
        try:
            is_locked, unlock_time, total_viewed, last_session = await self._check_targeted_search_lock(user_id)

            time_until_unlock = None
            if unlock_time:
                time_until_unlock = int((unlock_time - datetime.utcnow()).total_seconds())

            return SearchLockInfoResponse(
                user_id=user_id,
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

            result = await self.own_db.execute(stmt)
            sessions = result.scalars().all()

            return [
                SearchSessionResponse(
                    search_session_id=session.id,
                    search_type=session.search_type,
                    filters=session.filters,
                    results=session.results or [],
                    viewed_profiles=session.viewed_profiles or [],
                    current_page=session.current_page,
                    total_pages=session.total_pages,
                    total_results=session.total_results,
                    created_at=session.created_at,
                    updated_at=session.updated_at
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
            result = await self.own_db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                raise SearchSessionNotFoundException(f"Search session {session_id} not found")

            return SearchSessionResponse(
                search_session_id=session.id,
                search_type=session.search_type,
                filters=session.filters,
                results=session.results or [],
                viewed_profiles=session.viewed_profiles or [],
                current_page=session.current_page,
                total_pages=session.total_pages,
                total_results=session.total_results,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
        except SearchSessionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get search session {session_id}: {str(e)}")
            raise DatabaseException(f"Failed to get search session: {str(e)}")

    async def get_profiles_count(self) -> int:
        """Получение общего количества профилей"""
        try:
            stmt = select(func.count()).select_from(BasicProfile)
            result = await self.profile_db.execute(stmt)
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Failed to get profiles count: {str(e)}")
            raise DatabaseException(f"Failed to get profiles count: {str(e)}")

    async def delete_search_history(self, user_id: int, older_than_days: int = 30) -> int:
        """Удаление старой истории поиска (для cleanup задач)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            stmt = select(SearchSession).where(
                and_(
                    SearchSession.user_id == user_id,
                    SearchSession.created_at < cutoff_date
                )
            )

            result = await self.own_db.execute(stmt)
            sessions = result.scalars().all()

            for session in sessions:
                await self.own_db.delete(session)

            await self.own_db.commit()

            deleted_count = len(sessions)
            logger.info(f"Deleted {deleted_count} old search sessions for user {user_id}")

            return deleted_count
        except Exception as e:
            await self.own_db.rollback()
            logger.error(f"Failed to delete search history for user {user_id}: {str(e)}")
            raise DatabaseException(f"Failed to delete search history: {str(e)}")