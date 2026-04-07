import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update, and_
from sqlalchemy.exc import IntegrityError

from app.database.models import Swipe, Match, TargetedSearchLock
from app.schemas.swipe import SwipeResponse
from app.schemas.match import MatchResponse, PartnerInfo
from app.schemas.recommendation import (
    ClassicRecommendationFilters,
    TargetedRecommendationFilters,
    RecommendationProfile,
    RecommendationListResponse
)
from app.schemas.pagination import PaginationInfo
from app.schemas.lock import TargetedSearchLockInfo
from app.services.profile_client import profile_client
from app.services.redis_cache import redis_cache
from app.services.rabbitmq import event_publisher
from app.core.config import settings
from app.core.exceptions import (
    SwipeLimitExceededException,
    AlreadySwipedException,
    UserNotFoundException,
    DatabaseException,
    TargetedSearchLockedException
)
from app.core.logger import logger


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- Вспомогательные методы ----------
    
    async def _check_user_exists(self, user_id: str) -> bool:
        """Проверяет существование пользователя через profile-service."""
        try:
            profile = await profile_client.get_basic_profile(user_id)
            return profile is not None
        except Exception as e:
            logger.error(f"Failed to check user existence for {user_id}: {e}")
            return False
    
    async def _validate_users_exist(self, user_ids: List[str]) -> None:
        """Проверяет существование всех указанных пользователей."""
        for user_id in user_ids:
            if not await self._check_user_exists(user_id):
                raise UserNotFoundException(f"Пользователь {user_id} не найден")
    
    async def _get_users_who_disliked_me(self, user_id: str) -> List[str]:
        """Возвращает список пользователей, которые поставили ДИЗЛАЙК текущему пользователю."""
        stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'dislike'
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    # ---------- Управление блокировкой таргетированного поиска (по просмотрам) ----------
    
    async def _get_or_create_lock(self, keycloak_id: str) -> TargetedSearchLock:
        """Получает существующую запись блокировки или создаёт новую."""
        stmt = select(TargetedSearchLock).where(TargetedSearchLock.keycloak_id == keycloak_id).with_for_update()
        result = await self.db.execute(stmt)
        lock = result.scalar_one_or_none()
        
        if not lock:
            lock = TargetedSearchLock(
                keycloak_id=keycloak_id,
                is_locked=False,
                profiles_viewed=0,
                period_start=datetime.utcnow()
            )
            self.db.add(lock)
            await self.db.flush()
        return lock
    
    async def _reset_lock_if_expired(self, lock: TargetedSearchLock) -> bool:
        """Сбрасывает блокировку и счётчик, если истёк период блокировки или новый день."""
        now = datetime.utcnow()
        reset_needed = False
        
        # Если заблокирован и время блокировки истекло
        if lock.is_locked and lock.locked_until and lock.locked_until <= now:
            lock.is_locked = False
            lock.locked_until = None
            reset_needed = True
        
        # Сброс ежедневного счётчика (если прошло больше 24 часов с начала периода)
        if lock.period_start and (now - lock.period_start).total_seconds() >= 86400:
            lock.profiles_viewed = 0
            lock.period_start = now
            reset_needed = True
        elif not lock.period_start:
            lock.period_start = now
            reset_needed = True
        
        if reset_needed:
            await self.db.flush()
        return reset_needed
    
    async def _increment_views(self, keycloak_id: str, views_count: int = 1) -> Tuple[int, bool, Optional[datetime]]:
        """
        Увеличивает счётчик просмотренных профилей и проверяет блокировку.
        Возвращает (текущее_количество_просмотров, заблокирован_ли, время_разблокировки)
        """
        lock = await self._get_or_create_lock(keycloak_id)
        await self._reset_lock_if_expired(lock)
        
        # Если уже заблокирован – не увеличиваем
        if lock.is_locked:
            return lock.profiles_viewed, True, lock.locked_until
        
        # Увеличиваем счётчик
        lock.profiles_viewed += views_count
        
        # Проверяем превышение лимита
        if lock.profiles_viewed >= settings.limits.daily_limit:
            lock.is_locked = True
            lock.locked_until = datetime.utcnow() + timedelta(hours=settings.limits.targeted_lock_hours)
            logger.warning(
                f"User {keycloak_id[:8]}... reached daily targeted search limit ({lock.profiles_viewed}/{settings.limits.daily_limit}). "
                f"Locked until {lock.locked_until}"
            )
        
        await self.db.flush()
        return lock.profiles_viewed, lock.is_locked, lock.locked_until
    
    async def get_remaining_views(self, keycloak_id: str) -> int:
        """Возвращает количество оставшихся просмотров на сегодня для таргетированного поиска."""
        lock = await self._get_or_create_lock(keycloak_id)
        await self._reset_lock_if_expired(lock)
        remaining = max(0, settings.limits.daily_limit - lock.profiles_viewed)
        return remaining
    
    async def get_lock_status(self, keycloak_id: str) -> TargetedSearchLockInfo:
        """Возвращает статус блокировки для пользователя (только чтение, без изменений)."""
        lock = await self._get_or_create_lock(keycloak_id)
        # Не сбрасываем блокировку здесь, чтобы не изменять данные при GET-запросе
        
        time_until_unlock = None
        if lock.is_locked and lock.locked_until:
            delta = lock.locked_until - datetime.utcnow()
            time_until_unlock = max(0, int(delta.total_seconds()))
        
        return TargetedSearchLockInfo(
            is_locked=lock.is_locked,
            profiles_viewed=lock.profiles_viewed,
            daily_limit=settings.limits.daily_limit,
            locked_until=lock.locked_until,
            time_until_unlock=time_until_unlock
        )
    
    # ---------- Swipe (без влияния на блокировку) ----------
    
    async def swipe(self, from_user_id: str, to_user_id: str, action: str) -> SwipeResponse:
        """Создание свайпа (не влияет на блокировку таргетированного поиска)."""
        if from_user_id == to_user_id:
            raise UserNotFoundException("Нельзя свайпнуть самого себя")
        
        # Проверка существования пользователей
        if not await self._check_user_exists(to_user_id):
            raise UserNotFoundException(f"Целевой пользователь {to_user_id} не найден")
        if not await self._check_user_exists(from_user_id):
            raise UserNotFoundException(f"Текущий пользователь {from_user_id} не найден")
        
        # Попытка вставки свайпа
        try:
            new_swipe = Swipe(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                swipe_type=action
            )
            self.db.add(new_swipe)
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            stmt = select(Swipe).where(
                Swipe.from_user_id == from_user_id,
                Swipe.to_user_id == to_user_id
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise AlreadySwipedException(f"Вы уже {existing.swipe_type}d этого пользователя")
            raise
        
        # Проверка на взаимный лайк
        mutual_stmt = select(Swipe).where(
            Swipe.from_user_id == to_user_id,
            Swipe.to_user_id == from_user_id,
            Swipe.swipe_type == 'like'
        )
        mutual_result = await self.db.execute(mutual_stmt)
        mutual_like = mutual_result.scalar_one_or_none()
        
        if mutual_like and action == 'like':
            # Создание матча
            user1, user2 = sorted([from_user_id, to_user_id])
            new_match = Match(user1_id=user1, user2_id=user2, is_active=True)
            self.db.add(new_match)
            await self.db.commit()
            await self.db.refresh(new_match)
            
            # Публикация события о матче
            try:
                await event_publisher.publish_match_created(from_user_id, to_user_id)
            except Exception as e:
                logger.error(f"Failed to publish match event: {e}")
            
            return SwipeResponse(match=True, match_id=new_match.id, chat_id=None)
        else:
            await self.db.commit()
            return SwipeResponse(match=False)

    # ---------- Match list ----------
    
    async def get_matches(self, user_id: str, page: int = 1, limit: int = 20) -> Tuple[List[MatchResponse], int]:
        """Получение списка матчей с проверкой существования пользователя."""
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")
        
        offset = (page - 1) * limit
        stmt = select(Match).where(
            and_(
                (Match.user1_id == user_id) | (Match.user2_id == user_id),
                Match.is_active == True
            )
        ).order_by(Match.matched_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        matches = result.scalars().all()
        
        total_stmt = select(func.count()).where(
            and_(
                (Match.user1_id == user_id) | (Match.user2_id == user_id),
                Match.is_active == True
            )
        )
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        match_responses = []
        for match in matches:
            partner_id = match.user2_id if match.user1_id == user_id else match.user1_id
            profile = await profile_client.get_basic_profile(partner_id)
            if profile:
                display_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
                if not display_name:
                    display_name = partner_id[:8]
                partner_info = PartnerInfo(
                    keycloak_id=partner_id,
                    display_name=display_name,
                    avatar_url=profile.get('avatar_url')
                )
            else:
                partner_info = PartnerInfo(
                    keycloak_id=partner_id,
                    display_name=partner_id[:8],
                    avatar_url=None
                )
            match_responses.append(MatchResponse(
                match_id=match.id,
                partner=partner_info,
                matched_at=match.matched_at
            ))
        return match_responses, total

    # ---------- Swipe status ----------
    
    async def get_swipe_status(self, from_user_id: str, to_user_id: str) -> Dict[str, Any]:
        """Получение статуса свайпа с проверкой существования пользователей."""
        await self._validate_users_exist([from_user_id, to_user_id])
        stmt = select(Swipe).where(
            Swipe.from_user_id == from_user_id,
            Swipe.to_user_id == to_user_id
        )
        result = await self.db.execute(stmt)
        swipe = result.scalar_one_or_none()
        if swipe:
            return {"swiped": True, "type": swipe.swipe_type}
        return {"swiped": False, "type": None}

    # ---------- Reset (admin) ----------
    
    async def reset_user_data(self, user_id: str) -> Dict[str, int]:
        """Сброс всех данных пользователя (свайпы и блокировка)."""
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")
        
        # Удаляем все свайпы пользователя
        swipe_stmt = delete(Swipe).where(Swipe.from_user_id == user_id)
        swipe_result = await self.db.execute(swipe_stmt)
        
        # Сбрасываем блокировку
        lock_stmt = update(TargetedSearchLock).where(TargetedSearchLock.keycloak_id == user_id).values(
            is_locked=False,
            locked_until=None,
            profiles_viewed=0,
            period_start=datetime.utcnow()
        )
        await self.db.execute(lock_stmt)
        await self.db.commit()
        
        return {
            "swipes_deleted": swipe_result.rowcount
        }

    # ---------- Recommendations ----------
    
    async def get_incoming_likes(self, user_id: str) -> List[str]:
        """Возвращает список пользователей, которые лайкнули текущего, но он ещё не ответил."""
        likes_stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'like'
        )
        likes_result = await self.db.execute(likes_stmt)
        likers = [row[0] for row in likes_result.all()]
        
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped = [row[0] for row in swiped_result.all()]
        
        incoming = [uid for uid in likers if uid not in swiped]
        return incoming

    async def get_classic_recommendations(
        self,
        user_id: str,
        filters: ClassicRecommendationFilters,
        page: int = 1,
        limit: int = 10
    ) -> RecommendationListResponse:
        """
        Классические рекомендации на основе базовых фильтров.
        Не влияют на блокировку и не блокируются.
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")
        
        # Кого я уже свайпнул
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]
        
        # Кто поставил мне дизлайк
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids + [user_id]))
        
        # Входящие лайки
        incoming_likes = await self.get_incoming_likes(user_id)
        
        # Запрос к profile-service
        fetch_limit = limit + len(incoming_likes)
        result = await profile_client.search_profiles(
            gender=filters.gender.value if filters.gender else None,
            min_age=filters.min_age,
            max_age=filters.max_age,
            city=filters.city,
            exclude_keycloak_ids=all_exclude_ids,
            page=1,
            limit=fetch_limit
        )
        
        profiles_data = result.get("profiles", [])
        
        # Конвертируем в RecommendationProfile
        recommendations = []
        for p in profiles_data:
            basic = p.get("basic", {})
            age = self._calculate_age(basic.get("date_of_birth"))
            rec = RecommendationProfile(
                keycloak_id=basic.get("keycloak_id"),
                display_name=f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip() or basic.get('keycloak_id', '')[:8],
                age=age,
                city=basic.get("city", ""),
                avatar_url=basic.get("thumbnail_url")
            )
            recommendations.append(rec)
        
        # Перемешиваем для случайного порядка
        random.shuffle(recommendations)
        
        # Добавляем входящие лайки в начало (без дубликатов)
        incoming_profiles = []
        for like_user_id in incoming_likes:
            if like_user_id not in all_exclude_ids and like_user_id not in [r.keycloak_id for r in recommendations]:
                profile = await profile_client.get_basic_profile(like_user_id)
                if profile:
                    age = self._calculate_age(profile.get('date_of_birth'))
                    incoming_profiles.append(RecommendationProfile(
                        keycloak_id=like_user_id,
                        display_name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or like_user_id[:8],
                        age=age,
                        city=profile.get('city', ''),
                        avatar_url=profile.get('thumbnail_url')
                    ))
        
        all_recs = incoming_profiles + recommendations
        total = len(all_recs)
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        # Пагинация
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_recs = all_recs[start_idx:end_idx]
        
        pagination = PaginationInfo(
            current_page=page,
            total_pages=total_pages,
            total_results=total,
            page_size=limit
        )
        
        return RecommendationListResponse(profiles=paginated_recs, pagination=pagination, lock_info=None)

    async def get_targeted_recommendations(
        self,
        user_id: str,
        filters: TargetedRecommendationFilters,
        page: int = 1,
        limit: int = 10
    ) -> RecommendationListResponse:
        """
        Таргетированные рекомендации на основе эмбеддингов.
        Блокируются по количеству просмотренных профилей.
        При каждом запросе увеличивается счётчик просмотров.
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")
        
        # Проверяем блокировку и оставшиеся просмотры
        lock_status = await self.get_lock_status(user_id)
        if lock_status.is_locked:
            raise TargetedSearchLockedException(
                message=f"Таргетированный поиск заблокирован. Просмотрено {lock_status.profiles_viewed}/{lock_status.daily_limit} профилей. "
                        f"Разблокировка через {lock_status.time_until_unlock // 60} минут",
                unlock_time=lock_status.locked_until,
                time_until_unlock=lock_status.time_until_unlock,
                swipes_used=lock_status.profiles_viewed,
                daily_limit=lock_status.daily_limit
            )
        
        # Ограничиваем limit оставшимися просмотрами
        remaining = lock_status.daily_limit - lock_status.profiles_viewed
        effective_limit = min(limit, remaining)
        if effective_limit <= 0:
            raise TargetedSearchLockedException(
                message="У вас не осталось просмотров на сегодня для таргетированного поиска.",
                swipes_used=lock_status.profiles_viewed,
                daily_limit=lock_status.daily_limit
            )
        
        # Кого я уже свайпнул
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]
        
        # Кто поставил мне дизлайк
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids + [user_id]))
        
        # Входящие лайки (наивысший приоритет)
        incoming_likes = await self.get_incoming_likes(user_id)
        
        # Получаем эмбеддинг пользователя
        embedding = await redis_cache.get(f"embedding:{user_id}")
        if not embedding:
            embedding = await profile_client.get_embedding(user_id)
            if embedding:
                await redis_cache.set(f"embedding:{user_id}", embedding, ttl_seconds=3600)
            else:
                logger.warning(f"No embedding for user {user_id}, returning empty")
                return RecommendationListResponse(
                    profiles=[],
                    pagination=PaginationInfo(current_page=page, total_pages=1, total_results=0, page_size=limit),
                    lock_info=lock_status
                )
        
        # Запрос к profile-service через эмбеддинг
        profile_filters = {
            "gender": filters.gender.value if filters.gender else None,
            "min_age": filters.min_age,
            "max_age": filters.max_age,
            "city": filters.city,
            "education": filters.education,
            "hobbies_keywords": filters.hobbies_keywords,
            "online_only": filters.online_only
        }
        
        # Запрашиваем больше, чтобы учесть входящие лайки
        fetch_limit = effective_limit + len(incoming_likes)
        results = await profile_client.search_by_embedding(
            embedding=embedding,
            filters=profile_filters,
            exclude_ids=all_exclude_ids,
            limit=fetch_limit,
            offset=0
        )
        
        # Конвертируем в RecommendationProfile
        recommendations = []
        for item in results:
            rec = RecommendationProfile(
                keycloak_id=item['keycloak_id'],
                display_name=f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item['keycloak_id'][:8],
                age=item.get('age', 0),
                city=item.get('city', ''),
                avatar_url=item.get('thumbnail_url'),
                similarity=item.get('similarity')
            )
            recommendations.append(rec)
        
        # Добавляем входящие лайки в начало (без дубликатов)
        incoming_profiles = []
        for like_user_id in incoming_likes:
            if like_user_id not in all_exclude_ids and like_user_id not in [r.keycloak_id for r in recommendations]:
                profile = await profile_client.get_basic_profile(like_user_id)
                if profile:
                    age = self._calculate_age(profile.get('date_of_birth'))
                    incoming_profiles.append(RecommendationProfile(
                        keycloak_id=like_user_id,
                        display_name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or like_user_id[:8],
                        age=age,
                        city=profile.get('city', ''),
                        avatar_url=profile.get('thumbnail_url'),
                        similarity=1.0
                    ))
        
        all_recs = incoming_profiles + recommendations
        
        # Ограничиваем количество возвращаемых профилей effective_limit
        paginated_recs = all_recs[:effective_limit]
        total_returned = len(paginated_recs)
        
        # Увеличиваем счётчик просмотров на количество возвращённых профилей
        if total_returned > 0:
            views_count, is_locked, locked_until = await self._increment_views(user_id, total_returned)
        else:
            views_count, is_locked, locked_until = await self._increment_views(user_id, 0)
        
        # СОХРАНЯЕМ ИЗМЕНЕНИЯ В БАЗЕ ДАННЫХ
        await self.db.commit()
        
        # Получаем обновлённый статус блокировки
        final_lock_status = await self.get_lock_status(user_id)
        
        # Пагинация (упрощённая, так как мы возвращаем только одну "страницу")
        total_pages = 1
        pagination = PaginationInfo(
            current_page=page,
            total_pages=total_pages,
            total_results=total_returned,
            page_size=effective_limit
        )
        
        return RecommendationListResponse(
            profiles=paginated_recs, 
            pagination=pagination, 
            lock_info=final_lock_status
        )

    @staticmethod
    def _calculate_age(birth_date_str: Optional[str]) -> int:
        """Расчёт возраста по дате рождения."""
        if not birth_date_str:
            return 0
        try:
            birth = datetime.fromisoformat(birth_date_str).date()
            today = datetime.utcnow().date()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return max(0, age)
        except:
            return 0