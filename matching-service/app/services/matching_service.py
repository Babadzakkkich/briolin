import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, update
from sqlalchemy.exc import IntegrityError

from app.database.models import Swipe, Match
from app.schemas.swipe import SwipeResponse
from app.schemas.match import MatchResponse, PartnerInfo
from app.schemas.recommendation import (
    ClassicRecommendationFilters,
    TargetedRecommendationFilters,
    RecommendationProfile
)
from app.services.profile_client import profile_client
from app.services.search_client import search_client
from app.services.redis_cache import redis_cache
from app.services.rabbitmq import event_publisher
from app.core.config import settings
from app.core.exceptions import (
    SwipeLimitExceededException,
    AlreadySwipedException,
    UserNotFoundException,
    DatabaseException
)
from app.core.logger import logger


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- Вспомогательные методы ----------
    
    async def _check_user_exists(self, user_id: str) -> bool:
        """
        Проверяет существование пользователя через profile-service.
        Возвращает True если пользователь существует, иначе False.
        """
        try:
            profile = await profile_client.get_basic_profile(user_id)
            return profile is not None
        except Exception as e:
            logger.error(f"Failed to check user existence for {user_id}: {e}")
            return False
    
    async def _validate_users_exist(self, user_ids: List[str]) -> None:
        """
        Проверяет существование всех указанных пользователей.
        Выбрасывает UserNotFoundException если хотя бы один не существует.
        """
        for user_id in user_ids:
            if not await self._check_user_exists(user_id):
                raise UserNotFoundException(f"User {user_id} not found")
    
    async def _get_users_who_disliked_me(self, user_id: str) -> List[str]:
        """Возвращает список пользователей, которые поставили ДИЗЛАЙК текущему пользователю."""
        stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'dislike'
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    # ---------- Swipe ----------
    
    async def swipe(self, from_user_id: str, to_user_id: str, action: str) -> SwipeResponse:
        """Создание свайпа с проверкой существования пользователей"""
        
        # Проверка на свайп самого себя
        if from_user_id == to_user_id:
            raise UserNotFoundException("Cannot swipe on yourself")
        
        # Проверяем существование целевого пользователя
        if not await self._check_user_exists(to_user_id):
            raise UserNotFoundException(f"Target user {to_user_id} not found")
        
        # Проверяем существование текущего пользователя
        if not await self._check_user_exists(from_user_id):
            raise UserNotFoundException(f"Current user {from_user_id} not found")

        # Check daily limit
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        swipe_count_stmt = select(func.count()).where(
            Swipe.from_user_id == from_user_id,
            Swipe.created_at >= today_start
        )
        count_result = await self.db.execute(swipe_count_stmt)
        swipe_today = count_result.scalar_one()
        if swipe_today >= settings.limits.daily_limit:
            raise SwipeLimitExceededException()

        # Try to insert swipe
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
            # Already swiped - return existing status (no match)
            stmt = select(Swipe).where(
                Swipe.from_user_id == from_user_id,
                Swipe.to_user_id == to_user_id
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise AlreadySwipedException(f"Already {existing.swipe_type}d this user")
            raise

        # Check for mutual like
        mutual_stmt = select(Swipe).where(
            Swipe.from_user_id == to_user_id,
            Swipe.to_user_id == from_user_id,
            Swipe.swipe_type == 'like'
        )
        mutual_result = await self.db.execute(mutual_stmt)
        mutual_like = mutual_result.scalar_one_or_none()

        if mutual_like and action == 'like':
            # Create match
            user1, user2 = sorted([from_user_id, to_user_id])
            new_match = Match(user1_id=user1, user2_id=user2, is_active=True)
            self.db.add(new_match)
            await self.db.commit()
            await self.db.refresh(new_match)

            # Asynchronously publish match created event
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
        """Получение списка матчей с проверкой существования пользователя"""
        
        # Проверяем существование пользователя
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"User {user_id} not found")
        
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
                # Если профиль не найден, используем fallback
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
        """Получение статуса свайпа с проверкой существования пользователей"""
        
        # Проверяем существование пользователей
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

    # ---------- Reset swipes (admin) ----------
    
    async def reset_swipes(self, user_id: str) -> int:
        """Сброс свайпов пользователя с проверкой существования"""
        
        # Проверяем существование пользователя
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"User {user_id} not found")
        
        stmt = delete(Swipe).where(Swipe.from_user_id == user_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    # ---------- Recommendations ----------
    
    async def get_incoming_likes(self, user_id: str) -> List[str]:
        """Get list of users who liked current user and haven't been swiped back yet."""
        
        # Users who liked me
        likes_stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'like'
        )
        likes_result = await self.db.execute(likes_stmt)
        likers = [row[0] for row in likes_result.all()]

        # Users I already swiped on
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped = [row[0] for row in swiped_result.all()]

        # Incoming likes that I haven't responded to yet
        incoming = [uid for uid in likers if uid not in swiped]
        return incoming

    async def get_classic_recommendations(
        self,
        user_id: str,
        filters: ClassicRecommendationFilters,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[RecommendationProfile], int]:
        """
        Получение классических рекомендаций.
        
        Исключает:
        - Пользователей, на которых уже был сделан свайп (like/dislike)
        - Пользователей, которые поставили дизлайк текущему пользователю
        - Текущего пользователя
        
        Приоритет:
        1. Входящие лайки (кто лайкнул меня, но я ещё не ответил)
        2. Обычные рекомендации (случайный порядок)
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"User {user_id} not found")
        
        # 1. Кого я уже свайпнул (like или dislike)
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]
        
        # 2. Кто поставил мне дизлайк (исключаем их из рекомендаций)
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        
        # 3. Объединённый список исключений (без дубликатов)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids))
        
        logger.debug(f"User {user_id[:8]}... exclude_ids: {len(all_exclude_ids)} users")
        
        # 4. Получаем входящие лайки (наивысший приоритет)
        incoming_likes = await self.get_incoming_likes(user_id)
        
        # 5. Запрашиваем search-service с исключениями
        profiles_data = await search_client.classic_search(
            keycloak_id=user_id,
            gender=filters.gender.value if filters.gender else None,
            min_age=filters.min_age,
            max_age=filters.max_age,
            city=filters.city,
            exclude_ids=all_exclude_ids,
            limit=limit + len(incoming_likes),  # Запрашиваем больше, чтобы учесть входящие лайки
            offset=offset
        )
        
        # 6. Конвертируем в RecommendationProfile
        recommendations = []
        for p in profiles_data:
            age = p.get('age', 0)
            rec = RecommendationProfile(
                keycloak_id=p['keycloak_id'],
                display_name=f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or p['keycloak_id'][:8],
                age=age,
                city=p.get('city', ''),
                avatar_url=p.get('avatar_thumbnail_url')
            )
            recommendations.append(rec)
        
        # 7. Перемешиваем для случайного порядка (чтобы не было одинаковой выдачи)
        random.shuffle(recommendations)
        
        # 8. Добавляем входящие лайки в начало списка (без дубликатов)
        incoming_profiles = []
        for like_user_id in incoming_likes:
            # Проверяем, что пользователь не в исключениях и ещё не в списке
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
        
        # 9. Объединяем: сначала входящие лайки, потом остальные рекомендации
        all_recs = incoming_profiles + recommendations
        total = len(all_recs)
        
        # 10. Применяем пагинацию
        paginated = all_recs[offset:offset+limit]
        
        logger.info(f"Classic recommendations for {user_id[:8]}...: {len(paginated)} results (total: {total})")
        return paginated, total

    async def get_targeted_recommendations(
        self,
        user_id: str,
        filters: TargetedRecommendationFilters,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[RecommendationProfile], int]:
        """
        Получение таргетированных рекомендаций на основе эмбеддингов.
        
        Исключает:
        - Пользователей, на которых уже был сделан свайп (like/dislike)
        - Пользователей, которые поставили дизлайк текущему пользователю
        - Текущего пользователя
        
        Приоритет:
        1. Входящие лайки (кто лайкнул меня, но я ещё не ответил)
        2. Обычные рекомендации (сортировка по similarity от большего к меньшему)
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"User {user_id} not found")
        
        # 1. Кого я уже свайпнул (like или dislike)
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]
        
        # 2. Кто поставил мне дизлайк (исключаем их из рекомендаций)
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        
        # 3. Объединённый список исключений (без дубликатов)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids))
        
        logger.debug(f"User {user_id[:8]}... exclude_ids for targeted: {len(all_exclude_ids)} users")
        
        # 4. Получаем входящие лайки (наивысший приоритет)
        incoming_likes = await self.get_incoming_likes(user_id)
        
        # 5. Получаем эмбеддинг текущего пользователя (из кэша или profile-service)
        embedding = await redis_cache.get(f"embedding:{user_id}")
        if not embedding:
            embedding = await profile_client.get_embedding(user_id)
            if embedding:
                await redis_cache.set(f"embedding:{user_id}", embedding, ttl_seconds=3600)
                logger.debug(f"Embedding cached for user {user_id[:8]}...")
            else:
                logger.warning(f"No embedding for user {user_id}, returning empty")
                return [], 0
        
        # 6. Формируем фильтры для profile-service
        profile_filters = {
            "gender": filters.gender.value if filters.gender else None,
            "min_age": filters.min_age,
            "max_age": filters.max_age,
            "city": filters.city,
            "education": filters.education,
            "hobbies_keywords": filters.hobbies_keywords,
            "online_only": filters.online_only
        }
        
        # 7. Запрашиваем profile-service search_by_embedding с исключениями
        results = await profile_client.search_by_embedding(
            embedding=embedding,
            filters=profile_filters,
            exclude_ids=all_exclude_ids,
            limit=limit + len(incoming_likes),  # Запрашиваем больше, чтобы учесть входящие лайки
            offset=offset
        )
        
        # 8. Конвертируем в RecommendationProfile (уже отсортировано по similarity)
        recommendations = []
        for item in results:
            rec = RecommendationProfile(
                keycloak_id=item['keycloak_id'],
                display_name=f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item['keycloak_id'][:8],
                age=item.get('age', 0),
                city=item.get('city', ''),
                avatar_url=item.get('avatar_url'),
                similarity=item.get('similarity')
            )
            recommendations.append(rec)
        
        # 9. Добавляем входящие лайки в начало списка (без дубликатов)
        incoming_profiles = []
        for like_user_id in incoming_likes:
            # Проверяем, что пользователь не в исключениях и ещё не в списке
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
                        similarity=1.0  # Входящим лайкам даём максимальную схожесть
                    ))
        
        # 10. Объединяем: сначала входящие лайки, потом остальные рекомендации
        all_recs = incoming_profiles + recommendations
        total = len(all_recs)
        
        # 11. Применяем пагинацию
        paginated = all_recs[offset:offset+limit]
        
        logger.info(f"Targeted recommendations for {user_id[:8]}...: {len(paginated)} results (total: {total})")
        return paginated, total

    @staticmethod
    def _calculate_age(birth_date_str: Optional[str]) -> int:
        """Расчёт возраста по дате рождения"""
        if not birth_date_str:
            return 0
        try:
            birth = datetime.fromisoformat(birth_date_str).date()
            today = datetime.utcnow().date()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return max(0, age)
        except:
            return 0