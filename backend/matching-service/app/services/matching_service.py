from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.exceptions import (
    AlreadySwipedException,
    LikeLimitExceededException,
    MatchingServiceException,
    TargetedSearchLockedException,
    UserNotFoundException,
)
from app.core.logger import logger
from app.database.models import (
    DailyLikeUsage,
    LikeWithAnswers,
    Match,
    MatchWithAnswers,
    Swipe,
    TargetedSearchLock,
)
from app.schemas.lock import LikeUsageInfo, TargetedSearchLockInfo
from app.schemas.match import MatchResponse, PartnerInfo
from app.schemas.pagination import PaginationInfo
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationProfile,
    TargetedRecommendationFilters,
)
from app.schemas.search import (
    ClassicSearchFilters,
    SearchListResponse,
    SearchProfile,
    TargetedSearchFilters,
)
from app.schemas.swipe import SwipeResponse
from app.services.event_service import event_publisher
from app.services.profile_client import profile_client
from app.services.red_flag_checker import get_red_flag_checker
from app.services.redis_cache import redis_cache
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

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

    def _validate_answers(self, questions: Dict[str, str], answers: Dict[str, str]) -> None:
        """Валидация ответов на вопросы"""
        required_keys = ["question_1", "question_2", "question_3", "question_4", "question_5"]

        for key in required_keys:
            if key not in answers:
                raise MatchingServiceException(
                    message=f"Отсутствует ответ на вопрос: {key}",
                    status_code=400
                )
            if not answers[key] or not answers[key].strip():
                raise MatchingServiceException(
                    message=f"Ответ на вопрос {key} не может быть пустым",
                    status_code=400
                )
            if len(answers[key]) > 500:
                raise MatchingServiceException(
                    message=f"Ответ на вопрос {key} слишком длинный (макс. 500 символов)",
                    status_code=400
                )

    async def _ensure_has_questions(self, user_id: str) -> None:
        """
        Проверяет, что у пользователя заполнены все 5 вопросов.
        Если нет — выбрасывает исключение.
        """
        has_questions = await profile_client.has_questions(user_id)
        if not has_questions:
            raise MatchingServiceException(
                message="Для поиска и рекомендаций необходимо заполнить все 5 вопросов в профиле",
                status_code=403
            )

    async def _get_like_with_answers(
        self,
        from_user_id: str,
        to_user_id: str
    ) -> Optional[LikeWithAnswers]:
        """Получение существующего лайка с ответами"""
        stmt = select(LikeWithAnswers).where(
            and_(
                LikeWithAnswers.from_user_id == from_user_id,
                LikeWithAnswers.to_user_id == to_user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def _create_match_with_answers(
        self,
        user1_id: str,
        user2_id: str,
        user1_answers: Dict[str, str],
        user2_answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Создание мэтча с сохранением ответов.
        Также создает обычный мэтч для обратной совместимости.
        """
        user_a, user_b = sorted([user1_id, user2_id])
        is_user1_a = user1_id == user_a

        # Получаем вопросы обоих
        q1 = await profile_client.get_user_questions(user1_id)
        q2 = await profile_client.get_user_questions(user2_id)

        # Создаем мэтч с ответами
        match = MatchWithAnswers(
            user1_id=user_a,
            user2_id=user_b,
            user1_answers=user1_answers if is_user1_a else user2_answers,
            user2_answers=user2_answers if is_user1_a else user1_answers,
            user1_questions=q1 if is_user1_a else q2,
            user2_questions=q2 if is_user1_a else q1,
        )
        self.db.add(match)
        await self.db.flush()

        # Обновляем статусы лайков
        stmt = (
            update(LikeWithAnswers)
            .where(
                or_(
                    and_(
                        LikeWithAnswers.from_user_id == user1_id,
                        LikeWithAnswers.to_user_id == user2_id
                    ),
                    and_(
                        LikeWithAnswers.from_user_id == user2_id,
                        LikeWithAnswers.to_user_id == user1_id
                    )
                )
            )
            .values(status="matched")
        )
        await self.db.execute(stmt)

        await self.db.commit()

        logger.info(f"Match with answers created: {match.id} between {user1_id[:8]}... and {user2_id[:8]}...")

        # Публикуем событие о мэтче
        try:
            await event_publisher.publish_match_created(
                user1_id,
                user2_id,
                match_id=match.id
            )
        except Exception as e:
            logger.error(f"Failed to publish match event: {e}")

        return {
            "status": "matched",
            "message": "Взаимный лайк! мэтч создан.",
            "match_id": match.id,
            "show_answers": True,
            "answers": {
                "my_answers": user1_answers,
                "my_questions": q1,
                "partner_answers": user2_answers,
                "partner_questions": q2
            }
        }

    async def _get_users_who_disliked_me(self, user_id: str) -> List[str]:
        """Возвращает список пользователей, которые поставили ДИЗЛАЙК текущему пользователю."""
        stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'dislike'
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def _get_users_who_liked_me(self, user_id: str) -> List[str]:
        """Возвращает список пользователей, которые ЛАЙКНУЛИ текущего пользователя."""
        stmt = select(Swipe.from_user_id).where(
            Swipe.to_user_id == user_id,
            Swipe.swipe_type == 'like'
        )
        result = await self.db.execute(stmt)
        likers = [row[0] for row in result.all()]

        # Исключаем тех, на кого мы уже ответили
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped = [row[0] for row in swiped_result.all()]

        return [uid for uid in likers if uid not in swiped]

    # ========== УПРАВЛЕНИЕ ЛАЙКАМИ ==========

    async def _get_or_create_daily_like_usage(self, keycloak_id: str) -> DailyLikeUsage:
        """Получает или создаёт запись учёта лайков на сегодня."""
        today = datetime.utcnow().date()

        stmt = select(DailyLikeUsage).where(
            and_(
                DailyLikeUsage.keycloak_id == keycloak_id,
                DailyLikeUsage.usage_date == today
            )
        ).with_for_update()

        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()

        if not usage:
            usage = DailyLikeUsage(
                keycloak_id=keycloak_id,
                usage_date=today,
                likes_used=0
            )
            self.db.add(usage)
            await self.db.flush()

        return usage

    async def _check_and_increment_likes(self, keycloak_id: str) -> Tuple[int, int]:
        """
        Проверяет и увеличивает счётчик лайков.
        Возвращает (likes_used, daily_limit).
        Бросает LikeLimitExceededException при превышении лимита.
        """
        usage = await self._get_or_create_daily_like_usage(keycloak_id)

        if usage.likes_used >= settings.limits.daily_like_limit:
            raise LikeLimitExceededException(
                message=f"Дневной лимит лайков исчерпан ({usage.likes_used}/{settings.limits.daily_like_limit})",
                likes_used=usage.likes_used,
                daily_limit=settings.limits.daily_like_limit
            )

        usage.likes_used += 1
        await self.db.flush()

        logger.info(f"User {keycloak_id[:8]}... used like {usage.likes_used}/{settings.limits.daily_like_limit}")

        return usage.likes_used, settings.limits.daily_like_limit

    async def get_like_usage(self, keycloak_id: str) -> LikeUsageInfo:
        """Возвращает информацию об использовании лайков."""
        usage = await self._get_or_create_daily_like_usage(keycloak_id)

        return LikeUsageInfo(
            likes_used_today=usage.likes_used,
            daily_like_limit=settings.limits.daily_like_limit,
            likes_remaining=max(0, settings.limits.daily_like_limit - usage.likes_used)
        )

    async def _create_swipe(self, from_user_id: str, to_user_id: str, action: str) -> SwipeResponse:
        """
        Внутренний метод создания свайпа. Содержит всю логику мэтчинга.
        Не проверяет лимиты - это задача вызывающих методов.
        """
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
        if action == 'like':
            mutual_stmt = select(Swipe).where(
                Swipe.from_user_id == to_user_id,
                Swipe.to_user_id == from_user_id,
                Swipe.swipe_type == 'like'
            )
            mutual_result = await self.db.execute(mutual_stmt)
            mutual_like = mutual_result.scalar_one_or_none()

            if mutual_like:
                # Создание мэтча
                user1, user2 = sorted([from_user_id, to_user_id])
                new_match = Match(user1_id=user1, user2_id=user2, is_active=True)
                self.db.add(new_match)
                await self.db.commit()
                await self.db.refresh(new_match)

                # Публикация события о мэтче
                try:
                    await event_publisher.publish_match_created(from_user_id, to_user_id)
                except Exception as e:
                    logger.error(f"Failed to publish match event: {e}")

                return SwipeResponse(match=True, match_id=new_match.id, chat_id=None)

        await self.db.commit()
        return SwipeResponse(match=False)

    # ========== ПУБЛИЧНЫЕ МЕТОДЫ СВАЙПОВ ==========

    async def like_profile(self, from_user_id: str, to_user_id: str) -> SwipeResponse:
        """
        ⚠️ DEPRECATED: Старый метод лайка без вопросов.

        Теперь проверяет наличие вопросов у целевого пользователя.
        Если вопросы есть - требует использовать новый метод like_with_answers.
        """
        # Проверяем, есть ли вопросы у целевого пользователя
        has_questions = await profile_client.has_questions(to_user_id)

        if has_questions:
            raise MatchingServiceException(
                message="У пользователя есть вопросы. Используйте POST /api/v1/matching/like-with-answers",
                status_code=400
            )

        # Если вопросов нет - работаем по-старому
        await self._check_and_increment_likes(from_user_id)
        return await self._create_swipe(from_user_id, to_user_id, 'like')

    async def dislike_profile(self, from_user_id: str, to_user_id: str) -> SwipeResponse:
        """Поставить дизлайк профилю (без проверки лимита)."""
        return await self._create_swipe(from_user_id, to_user_id, 'dislike')

    async def like_with_answers(
        self,
        from_user_id: str,
        to_user_id: str,
        answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Лайк с обязательными ответами на вопросы.

        Flow:
        1. Проверяем, что у целевого пользователя есть вопросы
        2. Валидируем ответы (все 5 заполнены)
        3. Проверяем лимиты лайков
        4. Проверяем, не лайкали ли уже
        5. Проверяем взаимный лайк
        6. Если взаимно - создаем мэтч с ответами
        7. Если нет - сохраняем лайк с ответами
        """
        if from_user_id == to_user_id:
            raise UserNotFoundException("Нельзя лайкнуть самого себя")

        # Получаем вопросы целевого пользователя
        questions = await profile_client.get_user_questions(to_user_id)
        if not questions:
            raise MatchingServiceException(
                message="У пользователя нет вопросов. Используйте обычный лайк POST /api/v1/matching/like",
                status_code=400
            )

        # Валидируем ответы
        self._validate_answers(questions, answers)

        # Проверяем существование пользователей
        if not await self._check_user_exists(to_user_id):
            raise UserNotFoundException(f"Пользователь {to_user_id} не найден")
        if not await self._check_user_exists(from_user_id):
            raise UserNotFoundException(f"Пользователь {from_user_id} не найден")

        # Проверяем лимиты
        await self._check_and_increment_likes(from_user_id)

        # Проверяем существующий лайк
        existing = await self._get_like_with_answers(from_user_id, to_user_id)
        if existing:
            raise AlreadySwipedException("Вы уже отправили лайк этому пользователю")

        # Проверяем взаимный лайк
        reciprocal = await self._get_like_with_answers(to_user_id, from_user_id)

        if reciprocal and reciprocal.status == "pending":
            # ВЗАИМНЫЙ ЛАЙК - создаем мэтч
            return await self._create_match_with_answers(
                user1_id=from_user_id,
                user2_id=to_user_id,
                user1_answers=answers,
                user2_answers=reciprocal.answers
            )

        # Сохраняем лайк с ответами
        new_like = LikeWithAnswers(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            answers=answers,
            status="pending"
        )
        self.db.add(new_like)
        await self.db.commit()

        logger.info(f"Like with answers sent: {from_user_id[:8]}... -> {to_user_id[:8]}...")

        return {
            "status": "liked",
            "message": "Лайк с ответами отправлен. Ожидайте ответа.",
            "match_id": None,
            "show_answers": False
        }

    async def get_pending_likes(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Получение входящих лайков с ответами.
        Пользователь видит, кто его лайкнул и какие ответы дал.
        Теперь возвращает расширенную информацию о профиле отправителя.
        """
        # Получаем свои вопросы (для контекста)
        my_questions = await profile_client.get_user_questions(user_id)

        stmt = (
            select(LikeWithAnswers)
            .where(
                and_(
                    LikeWithAnswers.to_user_id == user_id,
                    LikeWithAnswers.status == "pending"
                )
            )
            .order_by(LikeWithAnswers.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        likes = result.scalars().all()

        pending = []
        for like in likes:
            # Получаем полный профиль отправителя (базовый + детальный)
            profile = await profile_client.get_full_profile_for_display(like.from_user_id)

            if profile:
                # Используем расширенный профиль
                like_info = {
                    "from_user_id": like.from_user_id,
                    "from_user_display_name": profile["display_name"],
                    "from_user_age": profile["age"],
                    "from_user_city": profile["city"],
                    "from_user_avatar": profile["avatar_url"],
                    "from_user_about_me": profile["about_me"],
                    "from_user_hobbies": profile["hobbies"],
                    "from_user_red_flags": profile["red_flags"],
                    "from_user_partner_preferences": profile["partner_preferences"],
                    "answers": like.answers,
                    "questions": my_questions,
                    "created_at": like.created_at.isoformat() if like.created_at else None
                }
            else:
                # Fallback: минимальная информация
                like_info = {
                    "from_user_id": like.from_user_id,
                    "from_user_display_name": like.from_user_id[:8],
                    "from_user_age": 0,
                    "from_user_city": "",
                    "from_user_avatar": None,
                    "from_user_about_me": "",
                    "from_user_hobbies": "",
                    "from_user_red_flags": [],
                    "from_user_partner_preferences": "",
                    "answers": like.answers,
                    "questions": my_questions,
                    "created_at": like.created_at.isoformat() if like.created_at else None
                }

            pending.append(like_info)

        return pending


    async def reverse_like_with_answers(
        self,
        user_id: str,
        from_user_id: str,
        answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Ответный лайк на входящий.
        Текущий пользователь отвечает на вопросы того, кто лайкнул первым.
        """
        # Получаем вопросы того, кто лайкнул первым
        questions = await profile_client.get_user_questions(from_user_id)
        if questions:
            self._validate_answers(questions, answers)

        # Проверяем входящий лайк
        incoming = await self._get_like_with_answers(from_user_id, user_id)
        if not incoming or incoming.status != "pending":
            raise MatchingServiceException(
                message="Входящий лайк не найден или уже обработан",
                status_code=404
            )

        # Проверяем лимиты
        await self._check_and_increment_likes(user_id)

        # Создаем мэтч
        return await self._create_match_with_answers(
            user1_id=user_id,
            user2_id=from_user_id,
            user1_answers=answers,
            user2_answers=incoming.answers
        )


    async def decline_like(self, user_id: str, from_user_id: str) -> bool:
        """Отклонить входящий лайк"""
        stmt = (
            update(LikeWithAnswers)
            .where(
                and_(
                    LikeWithAnswers.from_user_id == from_user_id,
                    LikeWithAnswers.to_user_id == user_id,
                    LikeWithAnswers.status == "pending"
                )
            )
            .values(status="declined")
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


    async def get_match_with_answers(
        self,
        match_id: int,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получение мэтча с ответами"""
        stmt = select(MatchWithAnswers).where(
            and_(
                MatchWithAnswers.id == match_id,
                MatchWithAnswers.is_active == True,
                or_(
                    MatchWithAnswers.user1_id == user_id,
                    MatchWithAnswers.user2_id == user_id
                )
            )
        )
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()

        if not match:
            return None

        # Определяем партнера
        is_user1 = match.user1_id == user_id
        partner_id = match.user2_id if is_user1 else match.user1_id

        # Получаем профиль партнера
        partner_profile = await profile_client.get_basic_profile(partner_id)
        partner_display_name = partner_id[:8]
        partner_avatar = None
        if partner_profile:
            first = partner_profile.get('first_name', '')
            last = partner_profile.get('last_name', '')
            partner_display_name = f"{first} {last}".strip() or partner_id[:8]
            partner_avatar = partner_profile.get('avatar_url') or partner_profile.get('thumbnail_url')

        return {
            "match_id": match.id,
            "partner": {
                "keycloak_id": partner_id,
                "display_name": partner_display_name,
                "avatar_url": partner_avatar
            },
            "matched_at": match.matched_at.isoformat() if match.matched_at else None,
            "my_answers": match.user1_answers if is_user1 else match.user2_answers,
            "my_questions": match.user1_questions if is_user1 else match.user2_questions,
            "partner_answers": match.user2_answers if is_user1 else match.user1_answers,
            "partner_questions": match.user2_questions if is_user1 else match.user1_questions,
        }

    # ========== УПРАВЛЕНИЕ БЛОКИРОВКОЙ ТАРГЕТИРОВАННЫХ РЕКОМЕНДАЦИЙ (ЭМБЕДДИНГИ) ==========

    async def _get_or_create_targeted_lock(self, keycloak_id: str) -> TargetedSearchLock:
        """Получает существующую запись блокировки или создаёт новую."""
        stmt = select(TargetedSearchLock).where(
            TargetedSearchLock.keycloak_id == keycloak_id
        ).with_for_update()
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

    async def _reset_targeted_lock_if_expired(self, lock: TargetedSearchLock) -> bool:
        """Сбрасывает блокировку и счётчик, если истёк период блокировки или новый день."""
        now = datetime.utcnow()
        reset_needed = False

        if lock.is_locked and lock.locked_until and lock.locked_until <= now:
            lock.is_locked = False
            lock.locked_until = None
            reset_needed = True

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

    async def _increment_targeted_views(self, keycloak_id: str, views_count: int = 1) -> Tuple[int, bool, Optional[datetime]]:
        """Увеличивает счётчик просмотренных профилей и проверяет блокировку."""
        lock = await self._get_or_create_targeted_lock(keycloak_id)
        await self._reset_targeted_lock_if_expired(lock)

        if lock.is_locked:
            return lock.profiles_viewed, True, lock.locked_until

        lock.profiles_viewed += views_count

        if lock.profiles_viewed >= settings.limits.targeted_daily_view_limit:
            lock.is_locked = True
            lock.locked_until = datetime.utcnow() + timedelta(hours=settings.limits.targeted_lock_hours)
            logger.warning(
                f"User {keycloak_id[:8]}... reached targeted view limit "
                f"({lock.profiles_viewed}/{settings.limits.targeted_daily_view_limit}). "
                f"Locked until {lock.locked_until}"
            )

        await self.db.flush()
        return lock.profiles_viewed, lock.is_locked, lock.locked_until

    async def get_targeted_lock_status(self, keycloak_id: str) -> TargetedSearchLockInfo:
        """Возвращает статус блокировки таргетированных рекомендаций."""
        lock = await self._get_or_create_targeted_lock(keycloak_id)

        time_until_unlock = None
        if lock.is_locked and lock.locked_until:
            delta = lock.locked_until - datetime.utcnow()
            time_until_unlock = max(0, int(delta.total_seconds()))

        return TargetedSearchLockInfo(
            is_locked=lock.is_locked,
            profiles_viewed=lock.profiles_viewed,
            daily_limit=settings.limits.targeted_daily_view_limit,
            locked_until=lock.locked_until,
            time_until_unlock=time_until_unlock
        )

    # ========== MATCHES ==========

    async def get_matches(self, user_id: str, page: int = 1, limit: int = 20) -> Tuple[List[MatchResponse], int]:
        """Получение списка мэтчей с проверкой существования пользователя."""
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

    # ========== SWIPE STATUS ==========

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

    # ========== RESET (ADMIN) ==========

    async def reset_user_data(self, user_id: str) -> Dict[str, int]:
        """Сброс всех данных пользователя (свайпы и блокировки)."""
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")

        swipe_stmt = delete(Swipe).where(Swipe.from_user_id == user_id)
        swipe_result = await self.db.execute(swipe_stmt)

        lock_stmt = update(TargetedSearchLock).where(
            TargetedSearchLock.keycloak_id == user_id
        ).values(
            is_locked=False,
            locked_until=None,
            profiles_viewed=0,
            period_start=datetime.utcnow()
        )
        await self.db.execute(lock_stmt)

        like_stmt = delete(DailyLikeUsage).where(DailyLikeUsage.keycloak_id == user_id)
        await self.db.execute(like_stmt)

        await self.db.commit()

        return {
            "swipes_deleted": swipe_result.rowcount
        }

    # ========== КЛАССИЧЕСКИЙ ПОИСК ==========

    async def classic_search(
        self,
        user_id: str,
        filters: ClassicSearchFilters,
        page: int = 1,
        limit: int = 10
    ) -> SearchListResponse:
        """
        Классический поиск на основе базовых фильтров.
        Без приоритета входящих лайков, без блокировок.
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")

        await self._ensure_has_questions(user_id)

        # Кого я уже свайпнул
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]

        # Кто поставил мне дизлайк
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids + [user_id]))

        # Запрос к profile-service
        result = await profile_client.search_profiles(
            gender=filters.gender.value if filters.gender else None,
            min_age=filters.min_age,
            max_age=filters.max_age,
            city=filters.city,
            exclude_keycloak_ids=all_exclude_ids,
            page=page,
            limit=limit
        )

        profiles_data = result.get("profiles", [])
        total = result.get("total", 0)
        total_pages = result.get("total_pages", 1)

        # Конвертируем в SearchProfile
        profiles = []
        for p in profiles_data:
            basic = p.get("basic", {})
            detailed = p.get("detailed")
            age = self._calculate_age(basic.get("date_of_birth"))

            prof = SearchProfile(
                keycloak_id=basic.get("keycloak_id"),
                display_name=f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip() or basic.get('keycloak_id', '')[:8],
                age=age,
                city=basic.get("city", ""),
                avatar_url=basic.get("thumbnail_url"),
                education=detailed.get("education") if detailed else None,
                hobbies=detailed.get("hobbies") if detailed else None
            )
            profiles.append(prof)

        pagination = PaginationInfo(
            current_page=page,
            total_pages=total_pages,
            total_results=total,
            page_size=limit
        )

        return SearchListResponse(profiles=profiles, pagination=pagination)

    # ========== ТАРГЕТИРОВАННЫЙ ПОИСК (БЕЗ ЭМБЕДДИНГОВ) ==========

    async def targeted_search(
        self,
        user_id: str,
        filters: TargetedSearchFilters,
        page: int = 1,
        limit: int = 10
    ) -> SearchListResponse:
        """
        Таргетированный поиск с расширенными фильтрами (без эмбеддингов).
        Без блокировки по просмотрам.
        """
        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")

        await self._ensure_has_questions(user_id)

        # Кого я уже свайпнул
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]

        # Кто поставил мне дизлайк
        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids + [user_id]))

        # Запрос к profile-service с расширенными фильтрами
        result = await profile_client.search_profiles(
            gender=filters.gender.value if filters.gender else None,
            min_age=filters.min_age,
            max_age=filters.max_age,
            city=filters.city,
            education=filters.education,
            hobbies_keywords=filters.hobbies_keywords,
            online_only=filters.online_only,
            exclude_keycloak_ids=all_exclude_ids,
            page=page,
            limit=limit
        )

        profiles_data = result.get("profiles", [])
        total = result.get("total", 0)
        total_pages = result.get("total_pages", 1)

        # Конвертируем в SearchProfile
        profiles = []
        for p in profiles_data:
            basic = p.get("basic", {})
            detailed = p.get("detailed")
            age = self._calculate_age(basic.get("date_of_birth"))

            prof = SearchProfile(
                keycloak_id=basic.get("keycloak_id"),
                display_name=f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip() or basic.get('keycloak_id', '')[:8],
                age=age,
                city=basic.get("city", ""),
                avatar_url=basic.get("thumbnail_url"),
                education=detailed.get("education") if detailed else None,
                hobbies=detailed.get("hobbies") if detailed else None
            )
            profiles.append(prof)

        pagination = PaginationInfo(
            current_page=page,
            total_pages=total_pages,
            total_results=total,
            page_size=limit
        )

        return SearchListResponse(profiles=profiles, pagination=pagination)

    # ========== ТАРГЕТИРОВАННЫЕ РЕКОМЕНДАЦИИ (ЭМБЕДДИНГИ) ==========

    async def get_targeted_recommendations(
        self,
        user_id: str,
        filters: TargetedRecommendationFilters,
        page: int = 1,
        limit: int = 10
    ) -> RecommendationListResponse:
        """
        Таргетированные рекомендации на основе эмбеддингов с автоматическими фильтрами.

        Автоматически определяются:
        - Пол: противоположный полу пользователя (для OTHER - все)
        - Возраст: ±5 лет от возраста пользователя (расширяется при малом количестве)
        - Город: из фильтров или город пользователя

        Блокируются по количеству просмотренных профилей.
        Фильтруются по Red Flags пользователя.
        Применяется тональный ре-ранкинг на основе sentiment embeddings.
        """

        if not await self._check_user_exists(user_id):
            raise UserNotFoundException(f"Пользователь {user_id} не найден")

        await self._ensure_has_questions(user_id)

        # Получаем профиль пользователя для автоматических фильтров
        user_profile = await profile_client.get_basic_profile(user_id)
        if not user_profile:
            raise UserNotFoundException(f"Профиль пользователя {user_id} не найден")

        user_age = self._calculate_age(user_profile.get('date_of_birth'))
        user_gender = user_profile.get('gender')
        user_city = user_profile.get('city')

        # Определяем пол для поиска
        if user_gender == 'male':
            target_gender = 'female'
        elif user_gender == 'female':
            target_gender = 'male'
        else:  # OTHER
            target_gender = None  # Все полы

        # Определяем город
        search_city = filters.city if filters.city else user_city

        # Определяем возрастной диапазон (начинаем с ±5)
        age_range = 5
        min_age = max(18, user_age - age_range)
        max_age = min(100, user_age + age_range)

        # Проверяем блокировку и оставшиеся просмотры
        lock_status = await self.get_targeted_lock_status(user_id)
        if lock_status.is_locked:
            raise TargetedSearchLockedException(
                message=f"Таргетированные рекомендации заблокированы. "
                        f"Просмотрено {lock_status.profiles_viewed}/{lock_status.daily_limit} профилей. "
                        f"Разблокировка через {lock_status.time_until_unlock // 60} минут",
                unlock_time=lock_status.locked_until,
                time_until_unlock=lock_status.time_until_unlock,
                profiles_viewed=lock_status.profiles_viewed,
                daily_limit=lock_status.daily_limit
            )

        remaining = lock_status.daily_limit - lock_status.profiles_viewed
        effective_limit = min(limit, remaining)
        if effective_limit <= 0:
            raise TargetedSearchLockedException(
                message="У вас не осталось просмотров на сегодня для таргетированных рекомендаций.",
                profiles_viewed=lock_status.profiles_viewed,
                daily_limit=lock_status.daily_limit
            )

        # Кого исключаем
        swiped_stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        swiped_result = await self.db.execute(swiped_stmt)
        swiped_ids = [row[0] for row in swiped_result.all()]

        disliked_by_ids = await self._get_users_who_disliked_me(user_id)
        all_exclude_ids = list(set(swiped_ids + disliked_by_ids + [user_id]))

        # Входящие лайки (наивысший приоритет)
        incoming_likes = await self._get_users_who_liked_me(user_id)

        # Получаем Red Flags пользователя для последующей фильтрации
        red_flag_checker = get_red_flag_checker()

        user_detailed = await profile_client.get_detailed_profile(user_id)
        user_red_flags = user_detailed.get("red_flags", []) if user_detailed else []

        # Получаем тональный эмбеддинг пользователя для ре-ранкинга
        user_sentiment_emb = await profile_client.get_sentiment_embedding(user_id)

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
                    pagination=PaginationInfo(
                        current_page=page, total_pages=1,
                        total_results=0, page_size=limit
                    ),
                    lock_info=lock_status,
                    sentiment_boost_applied=False,
                    applied_filters={
                        "gender": target_gender,
                        "city": search_city,
                        "min_age": min_age,
                        "max_age": max_age,
                        "age_range": age_range
                    }
                )

        # Функция для выполнения поиска с заданными параметрами
        async def do_search(min_age_val: int, max_age_val: int, city_val: Optional[str]) -> tuple:
            profile_filters = {
                "gender": target_gender,
                "min_age": min_age_val,
                "max_age": max_age_val,
                "city": city_val
            }

            fetch_limit = effective_limit * 3 + len(incoming_likes)
            results = await profile_client.search_by_embedding(
                embedding=embedding,
                filters=profile_filters,
                exclude_ids=all_exclude_ids,
                limit=fetch_limit,
                offset=0
            )
            return results, profile_filters

        # Первая попытка: с городом и возрастным диапазоном ±5
        results, applied_filters = await do_search(min_age, max_age, search_city)

        # Если мало результатов, пробуем расширить возраст до ±10
        if len(results) < effective_limit and age_range == 5:
            logger.info(f"Few results ({len(results)}) for user {user_id[:8]}..., expanding age range to ±10")
            age_range = 10
            min_age = max(18, user_age - age_range)
            max_age = min(100, user_age + age_range)
            results, applied_filters = await do_search(min_age, max_age, search_city)

        # Если и так мало, пробуем расширить возраст до ±15
        if len(results) < effective_limit and age_range <= 10:
            logger.info(f"Few results ({len(results)}) for user {user_id[:8]}..., expanding age range to ±15")
            age_range = 15
            min_age = max(18, user_age - age_range)
            max_age = min(100, user_age + age_range)
            results, applied_filters = await do_search(min_age, max_age, search_city)

        # ========== ФИЛЬТРАЦИЯ ПО RED FLAGS ==========
        red_flag_filtered_count = 0

        if user_red_flags and results:
            logger.info(
                f"Applying Red Flag filter for user {user_id[:8]}... "
                f"(red flags: {user_red_flags}, candidates: {len(results)})"
            )

            compatible_results = []

            for item in results:
                candidate_keycloak_id = item.get('keycloak_id')

                if not candidate_keycloak_id:
                    compatible_results.append(item)
                    continue

                try:
                    candidate_detailed = await profile_client.get_detailed_profile(candidate_keycloak_id)

                    if candidate_detailed:
                        candidate_text = red_flag_checker.get_profile_text({"detailed": candidate_detailed})

                        is_compatible, checks = await red_flag_checker.is_profile_compatible(
                            user_red_flags, candidate_text
                        )

                        if is_compatible:
                            compatible_results.append(item)
                        else:
                            red_flag_filtered_count += 1
                            conflict_flags = [c['red_flag'] for c in checks if c['conflict']]
                            logger.debug(
                                f"Red Flag: excluded candidate {candidate_keycloak_id[:8]}... "
                                f"for user {user_id[:8]}... "
                                f"(conflicts: {conflict_flags})"
                            )
                    else:
                        logger.debug(
                            f"Red Flag: no detailed profile for {candidate_keycloak_id[:8]}..., "
                            f"keeping in results"
                        )
                        compatible_results.append(item)

                except Exception as e:
                    logger.warning(
                        f"Red Flag check failed for {candidate_keycloak_id[:8]}...: {e}, "
                        f"keeping in results"
                    )
                    compatible_results.append(item)

            logger.info(
                f"Red Flag filtering complete: {len(results)} → {len(compatible_results)} "
                f"(filtered out: {red_flag_filtered_count})"
            )
            results = compatible_results

        # ========== ТОНАЛЬНЫЙ РЕ-РАНКИНГ ==========
        sentiment_boost_applied = False

        if user_sentiment_emb and results:
            logger.info(f"Applying sentiment re-ranking for {len(results)} candidates")

            for item in results:
                candidate_id = item.get('keycloak_id')

                try:
                    candidate_sentiment_emb = await profile_client.get_sentiment_embedding(candidate_id)

                    if candidate_sentiment_emb and len(candidate_sentiment_emb) == 3:
                        # user_sentiment_emb = [pos, neg, neu] для пользователя
                        # candidate_sentiment_emb = [pos, neg, neu] для кандидата

                        # Вычисляем тональную совместимость:
                        # 1. Если оба POSITIVE — высокая совместимость
                        # 2. Если оба NEGATIVE — средняя совместимость (общая нелюбовь)
                        # 3. Если один POSITIVE, другой NEGATIVE — низкая совместимость

                        user_pos = user_sentiment_emb[0]   # POSITIVE (индекс 0)
                        user_neg = user_sentiment_emb[1]   # NEGATIVE (индекс 1)
                        cand_pos = candidate_sentiment_emb[0]
                        cand_neg = candidate_sentiment_emb[1]

                        # Тональная совместимость: совпадение позитива + совпадение негатива
                        # Формула: pos_match + neg_match - pos_neg_mismatch
                        pos_match = user_pos * cand_pos           # оба позитивны
                        neg_match = user_neg * cand_neg           # оба негативны
                        mismatch = user_pos * cand_neg + user_neg * cand_pos  # противоположны

                        tonal_compatibility = pos_match + neg_match - mismatch
                        # Нормализуем в [-1, 1]
                        tonal_compatibility = max(-1.0, min(1.0, tonal_compatibility))

                        # Применяем к similarity
                        original_similarity = item.get('similarity', 0.0)
                        # 15% веса на тональность: повышаем при совместимости > 0, понижаем при < 0
                        boosted_similarity = original_similarity + (0.15 * tonal_compatibility)
                        boosted_similarity = max(0.0, min(1.0, boosted_similarity))

                        item['similarity'] = round(boosted_similarity, 4)
                        sentiment_boost_applied = True

                        logger.debug(
                            f"Sentiment boost for {candidate_id[:8]}...: "
                            f"{original_similarity:.3f} → {boosted_similarity:.3f} "
                            f"(tonal_compat={tonal_compatibility:.3f}, "
                            f"user=[P:{user_pos:.2f} N:{user_neg:.2f}], "
                            f"cand=[P:{cand_pos:.2f} N:{cand_neg:.2f}])"
                        )
                except Exception as e:
                    logger.debug(f"Failed to get sentiment for {candidate_id[:8]}...: {e}")

            if sentiment_boost_applied:
                results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
                logger.info("Sentiment re-ranking applied and results re-sorted")

        # ========== КОНВЕРТАЦИЯ В RECOMMENDATION PROFILE ==========

        recommendations = []
        max_age_diff = age_range

        for item in results:
            profile_age = item.get('age', 0)
            similarity = item.get('similarity', 0.0)

            age_diff = abs(profile_age - user_age)
            age_score = 1.0 - (age_diff / max_age_diff) if max_age_diff > 0 else 1.0
            age_score = max(0.0, min(1.0, age_score))

            combined_score = (0.8 * similarity) + (0.2 * age_score)

            rec = RecommendationProfile(
                keycloak_id=item['keycloak_id'],
                display_name=f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item['keycloak_id'][:8],
                age=profile_age,
                city=item.get('city', ''),
                avatar_url=item.get('thumbnail_url'),
                about_me=item.get('about_me'),
                hobbies=item.get('hobbies'),
                red_flags=item.get('red_flags'),
                partner_preferences=item.get('partner_preferences'),  # ДОБАВЛЯЕМ
                similarity=round(similarity, 4),
                combined_score=round(combined_score, 4),
            )
            recommendations.append(rec)

        # Добавляем входящие лайки в начало
        incoming_profiles = []
        existing_keys = {r.keycloak_id for r in recommendations}
        for like_user_id in incoming_likes:
            if like_user_id not in all_exclude_ids and like_user_id not in existing_keys:
                profile = await profile_client.get_basic_profile(like_user_id)
                if profile:
                    age = self._calculate_age(profile.get('date_of_birth'))

                    # Получаем детальный профиль для about_me, hobbies, red_flags, partner_preferences
                    detailed = await profile_client.get_detailed_profile(like_user_id)

                    incoming_profiles.append(RecommendationProfile(
                        keycloak_id=like_user_id,
                        display_name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or like_user_id[:8],
                        age=age,
                        city=profile.get('city', ''),
                        avatar_url=profile.get('thumbnail_url'),
                        about_me=detailed.get('about_me') if detailed else None,
                        hobbies=detailed.get('hobbies') if detailed else None,
                        red_flags=detailed.get('red_flags') if detailed else None,
                        partner_preferences=detailed.get('partner_preferences') if detailed else None,  # ДОБАВЛЯЕМ
                        similarity=1.0,
                        combined_score=1.0,
                    ))

        all_recs = incoming_profiles + recommendations

        paginated_recs = all_recs[:effective_limit]
        total_returned = len(paginated_recs)

        if total_returned > 0:
            views_count, is_locked, locked_until = await self._increment_targeted_views(user_id, total_returned)
        else:
            views_count, is_locked, locked_until = await self._increment_targeted_views(user_id, 0)

        await self.db.commit()

        final_lock_status = await self.get_targeted_lock_status(user_id)

        pagination = PaginationInfo(
            current_page=page,
            total_pages=1,
            total_results=total_returned,
            page_size=effective_limit
        )

        return RecommendationListResponse(
            profiles=paginated_recs,
            pagination=pagination,
            lock_info=final_lock_status,
            sentiment_boost_applied=sentiment_boost_applied,
            applied_filters={
                "gender": target_gender,
                "city": applied_filters.get("city"),
                "min_age": applied_filters.get("min_age"),
                "max_age": applied_filters.get("max_age"),
                "age_range": age_range,
                "user_age": user_age,
                "user_gender": user_gender,
                "user_city": user_city,
                "red_flag_filtered": red_flag_filtered_count,
                "user_red_flags": user_red_flags,
                "sentiment_boost_applied": sentiment_boost_applied
            }
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
