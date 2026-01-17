import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload  # ДОБАВЛЕНО
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    TestNotFoundException,
    TestAlreadyCompletedException,
    DailyLimitExceededException,
    TestTimeLimitExceededException,
    DatabaseException
)
from app.database.models import TestSession, TestResult, UserTestStatistics, TestStatus, PersonalityType
from app.database.session import mongo
from app.services.test_generator import get_test_generator
from app.services.scoring_service import get_scoring_service
from app.database.mongo_models import PersonalityDimension, TestTemplate, Question


class TestingService:
    """Основной сервис для работы с тестами"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.test_generator = get_test_generator()
        self.scoring_service = get_scoring_service()
    
    async def start_new_test(self, keycloak_id: str) -> Dict[str, Any]:
        """Начало нового теста для пользователя"""
        
        # Проверяем дневной лимит
        daily_attempts = await self._get_daily_attempts(keycloak_id)
        if daily_attempts >= settings.test_config.max_attempts_per_day:
            raise DailyLimitExceededException(
                f"Daily limit exceeded: {daily_attempts}/{settings.test_config.max_attempts_per_day}"
            )
        
        # Получаем активный шаблон теста
        template = await self.test_generator.get_active_test_template()
        
        # Генерируем вопросы для теста
        questions = await self.test_generator.generate_test_questions(template)
        
        # Создаем сессию теста
        test_session = TestSession(
            keycloak_id=keycloak_id,
            test_template_id=template.id,
            status=TestStatus.IN_PROGRESS,
            time_limit_minutes=template.time_limit_minutes,
            questions_order=[q.id for q in questions],
            user_answers={}
        )
        
        self.db.add(test_session)
        await self.db.commit()
        await self.db.refresh(test_session)
        
        # Обновляем статистику пользователя
        await self._update_user_statistics(keycloak_id, test_taken=True)
        
        # Формируем вопросы для отправки клиенту (без правильных ответов)
        questions_for_client = []
        for question in questions:
            question_dict = question.dict()
            
            # Убираем sensitive данные
            if "options" in question_dict:
                for option in question_dict["options"]:
                    if "score_impact" in option:
                        del option["score_impact"]
                    if "is_correct" in option:
                        del option["is_correct"]
            
            questions_for_client.append(question_dict)
        
        logger.info(f"Test session started for user {keycloak_id}: {test_session.id}")
        
        return {
            "session_id": str(test_session.id),
            "test_name": template.name,
            "description": template.description,
            "time_limit_minutes": template.time_limit_minutes,
            "questions": questions_for_client,
            "started_at": test_session.started_at.isoformat(),
            "expires_at": (
                test_session.started_at + timedelta(minutes=template.time_limit_minutes)
            ).isoformat()
        }
    
    async def submit_answer(
        self,
        session_id: uuid.UUID,
        keycloak_id: str,
        question_id: str,
        answer: Any
    ) -> Dict[str, Any]:
        """Сохранение ответа на вопрос"""
        
        # Получаем сессию теста
        test_session = await self._get_test_session(session_id, keycloak_id)
        
        # Проверяем, что тест еще активен
        if test_session.status != TestStatus.IN_PROGRESS:
            raise TestAlreadyCompletedException(
                f"Test session {session_id} is already {test_session.status}"
            )
        
        # Проверяем время
        if test_session.is_expired():
            test_session.status = TestStatus.EXPIRED
            await self.db.commit()
            raise TestTimeLimitExceededException(
                f"Test session {session_id} has expired"
            )
        
        # Проверяем, что вопрос есть в тесте
        if question_id not in test_session.questions_order:
            raise TestNotFoundException(
                f"Question {question_id} not found in test session {session_id}"
            )
        
        # ОБНОВЛЯЕМ объект test_session из базы
        await self.db.refresh(test_session)
        
        # Инициализируем user_answers если None
        if test_session.user_answers is None:
            test_session.user_answers = {}
        
        # Преобразуем JSON в dict если необходимо
        if isinstance(test_session.user_answers, str):
            test_session.user_answers = json.loads(test_session.user_answers)
        
        # Сохраняем ответ
        test_session.user_answers[question_id] = answer
        
        # Уведомляем SQLAlchemy об изменении JSON поля
        flag_modified(test_session, "user_answers")
        
        # Обновляем объект в базе
        await self.db.commit()
        # ОБЯЗАТЕЛЬНО обновляем объект после commit
        await self.db.refresh(test_session)
        
        logger.info(f"Answer saved for question {question_id} in session {session_id}. "
                   f"Total answered: {len(test_session.user_answers)}")
        
        return {
            "session_id": str(session_id),
            "question_id": question_id,
            "answer_saved": True,
            "total_answered": len(test_session.user_answers),
            "total_questions": len(test_session.questions_order)
        }
    
    async def complete_test(
        self,
        session_id: uuid.UUID,
        keycloak_id: str
    ) -> Dict[str, Any]:
        """Завершение теста и подсчет результатов"""
        
        # ИСПРАВЛЕНО: Загружаем сессию с результатом сразу
        test_session = await self._get_test_session_with_result(session_id, keycloak_id)
        
        # Проверяем статус
        if test_session.status == TestStatus.COMPLETED:
            # ИСПРАВЛЕНО: Проверяем, что result загружен
            if hasattr(test_session, 'result') and test_session.result:
                return await self._format_existing_results(test_session)
            else:
                # Пересчитываем результаты (должно быть редким случаем)
                return await self._calculate_and_save_results(test_session)
        
        if test_session.status != TestStatus.IN_PROGRESS:
            raise TestAlreadyCompletedException(
                f"Test session {session_id} is {test_session.status}"
            )
        
        # Преобразуем user_answers из JSON если необходимо
        user_answers = test_session.user_answers
        if isinstance(user_answers, str):
            user_answers = json.loads(user_answers)
        elif user_answers is None:
            user_answers = {}
        
        # Проверяем, что ответил на все вопросы
        answered_count = len(user_answers) if user_answers else 0
        total_questions = len(test_session.questions_order) if test_session.questions_order else 0
        
        logger.info(f"Test completion: {answered_count}/{total_questions} questions answered")
        
        # Получаем шаблон теста
        template_data = await mongo.test_templates.find_one(
            {"id": test_session.test_template_id}
        )
        if not template_data:
            raise TestNotFoundException(f"Template {test_session.test_template_id} not found")
        
        template = TestTemplate(**template_data)
        
        # Получаем вопросы
        questions = await self.test_generator.get_questions_by_ids(test_session.questions_order)
        
        # Подсчитываем баллы
        scores = await self.scoring_service.calculate_scores(
            questions, user_answers
        )
        
        logger.info(f"Scores calculated: {scores}")
        
        # Определяем типы личности
        try:
            primary, secondary = await self.scoring_service.determine_personality_types(scores)
            logger.info(f"Personality types determined: primary={primary}, secondary={secondary}")
        except Exception as e:
            logger.error(f"Error determining personality types: {e}")
            # Устанавливаем дефолтные значения
            primary = PersonalityType.ROMANTIC
            secondary = PersonalityType.ADVENTURER
        
        # Создаем результат теста
        test_result = TestResult(
            session_id=test_session.id,
            keycloak_id=keycloak_id,
            romantic_score=float(scores.get(PersonalityDimension.ROMANTIC, 0.0)),
            adventurer_score=float(scores.get(PersonalityDimension.ADVENTURER, 0.0)),
            intellectual_score=float(scores.get(PersonalityDimension.INTELLECTUAL, 0.0)),
            caregiver_score=float(scores.get(PersonalityDimension.CAREGIVER, 0.0)),
            leader_score=float(scores.get(PersonalityDimension.LEADER, 0.0)),
            free_spirit_score=float(scores.get(PersonalityDimension.FREE_SPIRIT, 0.0)),
            primary_personality=primary,
            secondary_personality=secondary,
            total_score=float(sum(scores.values())),
            max_possible_score=float(len(questions) * 3 * 10),
            percentage=float(min(100, (sum(scores.values()) / (len(questions) * 3 * 10)) * 100) if questions else 0)
        )
        
        # Генерируем интерпретацию
        try:
            test_result.interpretation = await self.scoring_service.generate_interpretation(
                scores, primary, secondary, template.personality_descriptions
            )
        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            test_result.interpretation = "Интерпретация результатов недоступна."
        
        # Генерируем рекомендации
        try:
            test_result.recommendations = await self.scoring_service.generate_recommendations(
                primary, secondary, template.recommendations
            )
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            test_result.recommendations = "Рекомендации недоступны."
        
        # Сохраняем результат
        self.db.add(test_result)
        
        # Обновляем сессию
        test_session.status = TestStatus.COMPLETED
        test_session.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(test_session)
        await self.db.refresh(test_result)
        
        # Обновляем статистику пользователя
        await self._update_user_statistics(
            keycloak_id,
            test_completed=True,
            primary_personality=primary
        )
        
        logger.info(f"Test completed for user {keycloak_id}: session {session_id}")
        
        return await self._format_results(test_session, test_result)
    
    async def get_test_results(
        self,
        session_id: uuid.UUID,
        keycloak_id: str
    ) -> Dict[str, Any]:
        """Получение результатов теста"""
        
        # ИСПРАВЛЕНО: Загружаем сразу с результатом
        test_session = await self._get_test_session_with_result(session_id, keycloak_id)
        
        if test_session.status != TestStatus.COMPLETED or not test_session.result:
            raise TestNotFoundException(f"No results for test session {session_id}")
        
        return await self._format_existing_results(test_session)
    
    async def get_user_test_history(
        self,
        keycloak_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Получение истории тестов пользователя"""
        
        # ИСПРАВЛЕНО: Загружаем сразу с результатами
        query = select(TestSession).options(
            selectinload(TestSession.result)
        ).where(
            TestSession.keycloak_id == keycloak_id,
            TestSession.status == TestStatus.COMPLETED
        ).order_by(TestSession.completed_at.desc())
        
        result = await self.db.execute(query.offset(skip).limit(limit))
        sessions = result.scalars().all()
        
        total_query = select(func.count(TestSession.id)).where(
            TestSession.keycloak_id == keycloak_id,
            TestSession.status == TestStatus.COMPLETED
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        history = []
        for session in sessions:
            if session.result:
                # ИСПРАВЛЕНО: Безопасное получение значений Enum
                primary = session.result.primary_personality
                secondary = session.result.secondary_personality
                
                primary_str = primary.value if isinstance(primary, PersonalityType) else str(primary)
                secondary_str = secondary.value if isinstance(secondary, PersonalityType) else str(secondary)
                
                history.append({
                    "session_id": str(session.id),
                    "test_name": "Personality Test",
                    "completed_at": session.completed_at.isoformat(),
                    "primary_personality": primary_str,
                    "secondary_personality": secondary_str,
                    "total_score": session.result.total_score,
                    "percentage": session.result.percentage
                })
        
        return {
            "history": history,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def get_user_statistics(
        self,
        keycloak_id: str
    ) -> Dict[str, Any]:
        """Получение статистики пользователя по тестам"""
        
        query = select(UserTestStatistics).where(
            UserTestStatistics.keycloak_id == keycloak_id
        )
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()
        
        if not stats:
            # Создаем начальную статистику
            stats = UserTestStatistics(keycloak_id=keycloak_id)
            self.db.add(stats)
            await self.db.commit()
            await self.db.refresh(stats)
        
        # Исправление: защита от None
        def safe_get(attr):
            value = getattr(stats, attr, 0)
            return value if value is not None else 0
        
        # ИСПРАВЛЕНО: Конвертируем Enum в строки для JSON сериализации
        distribution = stats.get_primary_personality_distribution()
        distribution_dict = {}
        for key, value in distribution.items():
            key_str = key.value if isinstance(key, PersonalityType) else str(key)
            distribution_dict[key_str] = value
        
        return {
            "total_tests_taken": safe_get("total_tests_taken"),
            "total_tests_completed": safe_get("total_tests_completed"),
            "average_score": stats.average_score if stats.average_score is not None else 0.0,
            "personality_distribution": distribution_dict,
            "last_test_date": stats.last_test_date.isoformat() if stats.last_test_date else None,
            "updated_at": stats.updated_at.isoformat() if stats.updated_at else None
        }
    
    # ИСПРАВЛЕНО: Новый метод, который сразу загружает сессию с результатом
    async def _get_test_session_with_result(
        self,
        session_id: uuid.UUID,
        keycloak_id: str
    ) -> TestSession:
        """Получение сессии теста с предзагрузкой результата"""
        query = select(TestSession).options(
            selectinload(TestSession.result)
        ).where(
            TestSession.id == session_id,
            TestSession.keycloak_id == keycloak_id
        )
        result = await self.db.execute(query)
        test_session = result.scalar_one_or_none()
        
        if not test_session:
            raise TestNotFoundException(f"Test session {session_id} not found")
        
        return test_session
    
    async def _get_test_session(
        self,
        session_id: uuid.UUID,
        keycloak_id: str
    ) -> TestSession:
        """Получение сессии теста с проверкой владельца"""
        query = select(TestSession).where(
            TestSession.id == session_id,
            TestSession.keycloak_id == keycloak_id
        )
        result = await self.db.execute(query)
        test_session = result.scalar_one_or_none()
        
        if not test_session:
            raise TestNotFoundException(f"Test session {session_id} not found")
        
        return test_session
    
    async def _get_daily_attempts(self, keycloak_id: str) -> int:
        """Получение количества попыток за сегодня"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        query = select(func.count(TestSession.id)).where(
            and_(
                TestSession.keycloak_id == keycloak_id,
                TestSession.started_at >= today_start,
                TestSession.started_at < today_end
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def _update_user_statistics(
        self,
        keycloak_id: str,
        test_taken: bool = False,
        test_completed: bool = False,
        primary_personality: Optional[PersonalityType] = None
    ):
        """Обновление статистики пользователя"""
        query = select(UserTestStatistics).where(
            UserTestStatistics.keycloak_id == keycloak_id
        )
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = UserTestStatistics(keycloak_id=keycloak_id)
            self.db.add(stats)
        
        # Исправление: защита от None
        if test_taken:
            current = stats.total_tests_taken
            if current is None:
                current = 0
            stats.total_tests_taken = current + 1
        
        if test_completed:
            current = stats.total_tests_completed
            if current is None:
                current = 0
            stats.total_tests_completed = current + 1
        
        if primary_personality:
            # Обновляем счетчик для основного типа личности
            def safe_increment(current_value):
                return (current_value or 0) + 1
            
            # ИСПРАВЛЕНО: Приводим к строке если это Enum
            personality_str = primary_personality.value if isinstance(primary_personality, PersonalityType) else str(primary_personality)
            
            if personality_str == PersonalityType.ROMANTIC.value:
                stats.primary_romantic_count = safe_increment(stats.primary_romantic_count)
            elif personality_str == PersonalityType.ADVENTURER.value:
                stats.primary_adventurer_count = safe_increment(stats.primary_adventurer_count)
            elif personality_str == PersonalityType.INTELLECTUAL.value:
                stats.primary_intellectual_count = safe_increment(stats.primary_intellectual_count)
            elif personality_str == PersonalityType.CAREGIVER.value:
                stats.primary_caregiver_count = safe_increment(stats.primary_caregiver_count)
            elif personality_str == PersonalityType.LEADER.value:
                stats.primary_leader_count = safe_increment(stats.primary_leader_count)
            elif personality_str == PersonalityType.FREE_SPIRIT.value:
                stats.primary_free_spirit_count = safe_increment(stats.primary_free_spirit_count)
        
        if test_completed:
            stats.last_test_date = datetime.utcnow()
        
        await self.db.commit()
    
    async def _format_results(
        self,
        test_session: TestSession,
        test_result: TestResult
    ) -> Dict[str, Any]:
        """Форматирование результатов для ответа"""
        # ИСПРАВЛЕНО: Безопасное получение значений Enum
        primary = test_result.primary_personality
        secondary = test_result.secondary_personality
        
        primary_str = primary.value if isinstance(primary, PersonalityType) else str(primary)
        secondary_str = secondary.value if isinstance(secondary, PersonalityType) else str(secondary)
        
        return {
            "session_id": str(test_session.id),
            "status": test_session.status.value if isinstance(test_session.status, TestStatus) else str(test_session.status),
            "completed_at": test_session.completed_at.isoformat(),
            "time_spent_minutes": (
                (test_session.completed_at - test_session.started_at).total_seconds() / 60
                if test_session.completed_at and test_session.started_at else None
            ),
            "results": {
                "primary_personality": primary_str,
                "secondary_personality": secondary_str,
                "personality_scores": test_result.personality_scores,
                "total_score": test_result.total_score,
                "max_possible_score": test_result.max_possible_score,
                "percentage": test_result.percentage,
                "interpretation": test_result.interpretation,
                "recommendations": test_result.recommendations
            },
            "summary": {
                "questions_total": len(test_session.questions_order) if test_session.questions_order else 0,
                "questions_answered": len(test_session.user_answers) if test_session.user_answers else 0,
                "completion_rate": (
                    (len(test_session.user_answers) / len(test_session.questions_order) * 100)
                    if test_session.questions_order and len(test_session.questions_order) > 0 else 0
                )
            }
        }
    
    async def _format_existing_results(self, test_session: TestSession) -> Dict[str, Any]:
        """Форматирование существующих результатов"""
        # ИСПРАВЛЕНО: Убеждаемся, что result загружен
        if not test_session.result:
            # Если result не загружен, подгружаем его
            await self.db.refresh(test_session, ['result'])
        
        return await self._format_results(test_session, test_session.result)
    
    async def _calculate_and_save_results(self, test_session: TestSession) -> Dict[str, Any]:
        """Пересчет и сохранение результатов (если результат потерян)"""
        raise DatabaseException("Test results need to be recalculated")