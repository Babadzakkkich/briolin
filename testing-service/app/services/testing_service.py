import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    TestNotFoundException,
    TestAlreadyCompletedException,
    DailyLimitExceededException,
    TestTimeLimitExceededException,
    DatabaseException,
    ActiveTestSessionExistsException
)
from app.database.models import TestSession, TestResult, TestStatus
from app.database.session import mongo
from app.services.test_generator import get_test_generator
from app.services.scoring_service import get_scoring_service
from app.services.event_service import get_testing_event_service
from app.database.mongo_models import Question


class TestingService:
    """Основной сервис для работы с тестами"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.test_generator = get_test_generator()
        self.scoring_service = get_scoring_service()
        self.event_service = get_testing_event_service()
    
    async def _get_active_session(self, keycloak_id: str) -> Optional[TestSession]:
        """Получение активной сессии теста для пользователя"""
        query = select(TestSession).options(
            selectinload(TestSession.result)
        ).where(
            and_(
                TestSession.keycloak_id == keycloak_id,
                TestSession.status == TestStatus.IN_PROGRESS
            )
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        # Проверяем не истекла ли сессия
        if session and session.is_expired():
            session.status = TestStatus.EXPIRED
            await self.db.commit()
            return None
        
        return session
    
    async def get_current_test(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение текущего активного теста пользователя"""
        active_session = await self._get_active_session(keycloak_id)
        
        if not active_session:
            return None
        
        # Получаем вопросы для отображения
        questions = await self.test_generator.get_questions_by_ids(
            active_session.questions_order
        )
        
        # СОХРАНЯЕМ ПОРЯДОК - создаем словарь для быстрого доступа по ID
        questions_dict = {q.id: q for q in questions}
        
        # Формируем вопросы для клиента в правильном порядке из questions_order
        questions_for_client = []
        for question_id in active_session.questions_order:
            question = questions_dict.get(question_id)
            if not question:
                logger.warning(f"Question {question_id} not found in database")
                continue
                
            question_dict = question.dict()
            
            # Убираем чувствительную информацию
            if "options" in question_dict:
                for option in question_dict["options"]:
                    option.pop("score", None)
                    option.pop("is_correct", None)
            
            # Добавляем информацию о том, отвечен ли вопрос
            question_dict["answered"] = question.id in (active_session.user_answers or {})
            
            # Добавляем сохраненный ответ, если есть
            if active_session.user_answers and question.id in active_session.user_answers:
                question_dict["saved_answer"] = active_session.user_answers[question.id]
            
            questions_for_client.append(question_dict)
        
        # Получаем шаблон теста для названия
        template = await self.test_generator.get_active_test_template()
        
        status_value = active_session.status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        elif isinstance(status_value, str):
            status_value = status_value
        else:
            status_value = str(status_value)
        
        return {
            "session_id": str(active_session.id),
            "test_name": template.name,
            "description": template.description,
            "status": status_value,
            "started_at": active_session.started_at.isoformat(),
            "expires_at": (
                active_session.started_at + timedelta(minutes=active_session.time_limit_minutes)
            ).isoformat(),
            "time_left_seconds": active_session.get_time_left_seconds(),
            "time_limit_minutes": active_session.time_limit_minutes,
            "total_questions": len(active_session.questions_order),
            "answered_questions": len(active_session.user_answers or {}),
            "questions": questions_for_client
        }
    
    async def start_new_test(self, keycloak_id: str) -> Dict[str, Any]:
        """Начало нового теста для пользователя"""
        
        # Проверяем наличие активной сессии
        active_session = await self._get_active_session(keycloak_id)
        if active_session:
            raise ActiveTestSessionExistsException(
                f"Active test session already exists: {active_session.id}",
                session_id=str(active_session.id)
            )
        
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
        
        # Сохраняем порядок вопросов
        questions_order = [q.id for q in questions]
        
        # Создаем сессию теста
        test_session = TestSession(
            keycloak_id=keycloak_id,
            test_template_id=template.id,
            status=TestStatus.IN_PROGRESS,
            time_limit_minutes=template.time_limit_minutes,
            questions_order=questions_order,  # Сохраняем порядок
            user_answers={}
        )
        
        try:
            self.db.add(test_session)
            await self.db.commit()
            await self.db.refresh(test_session)
        except IntegrityError as e:
            await self.db.rollback()
            # Если нарушено уникальное ограничение - значит активная сессия уже существует
            if "unique_active_session" in str(e):
                active = await self._get_active_session(keycloak_id)
                if active:
                    raise ActiveTestSessionExistsException(
                        f"Active test session already exists: {active.id}",
                        session_id=str(active.id)
                    )
            raise
        
        logger.info(f"Test session started for user {keycloak_id}: {test_session.id}")
        
        # Публикуем событие начала теста
        try:
            await self.event_service.publish_test_started(
                keycloak_id=keycloak_id,
                session_id=str(test_session.id),
                test_template_id=template.id
            )
        except Exception as e:
            logger.error(f"Failed to publish test started event: {e}")
        
        # Формируем вопросы для отправки клиенту (без баллов) в правильном порядке
        questions_for_client = []
        for question in questions:
            question_dict = question.dict()
            
            if "options" in question_dict:
                for option in question_dict["options"]:
                    option.pop("score", None)
                    option.pop("is_correct", None)
            
            question_dict["answered"] = False
            questions_for_client.append(question_dict)
        
        return {
            "session_id": str(test_session.id),
            "test_name": template.name,
            "description": template.description,
            "time_limit_minutes": template.time_limit_minutes,
            "questions": questions_for_client,
            "started_at": test_session.started_at.isoformat(),
            "expires_at": (
                test_session.started_at + timedelta(minutes=template.time_limit_minutes)
            ).isoformat(),
            "time_left_seconds": test_session.get_time_left_seconds()
        }
    
    async def submit_answer(
        self,
        session_id: uuid.UUID,
        keycloak_id: str,
        question_id: str,
        answer: Any
    ) -> Dict[str, Any]:
        """Сохранение ответа на вопрос"""
        
        test_session = await self._get_test_session(session_id, keycloak_id)
        
        if test_session.status != TestStatus.IN_PROGRESS:
            raise TestAlreadyCompletedException(
                f"Test session {session_id} is already {test_session.status}"
            )
        
        if test_session.is_expired():
            test_session.status = TestStatus.EXPIRED
            await self.db.commit()
            raise TestTimeLimitExceededException(
                f"Test session {session_id} has expired"
            )
        
        if question_id not in test_session.questions_order:
            raise TestNotFoundException(
                f"Question {question_id} not found in test session {session_id}"
            )
        
        await self.db.refresh(test_session)
        
        if test_session.user_answers is None:
            test_session.user_answers = {}
        
        if isinstance(test_session.user_answers, str):
            test_session.user_answers = json.loads(test_session.user_answers)
        
        test_session.user_answers[question_id] = answer
        flag_modified(test_session, "user_answers")
        
        await self.db.commit()
        await self.db.refresh(test_session)
        
        logger.info(
            f"Answer saved for question {question_id} in session {session_id}. "
            f"Total answered: {len(test_session.user_answers)}"
        )
        
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
        
        test_session = await self._get_test_session_with_result(session_id, keycloak_id)
        
        if test_session.status == TestStatus.COMPLETED:
            if hasattr(test_session, 'result') and test_session.result:
                return await self._format_existing_results(test_session)
            else:
                return await self._calculate_and_save_results(test_session)
        
        if test_session.status != TestStatus.IN_PROGRESS:
            raise TestAlreadyCompletedException(
                f"Test session {session_id} is {test_session.status}"
            )
        
        user_answers = test_session.user_answers
        if isinstance(user_answers, str):
            user_answers = json.loads(user_answers)
        elif user_answers is None:
            user_answers = {}
        
        answered_count = len(user_answers) if user_answers else 0
        total_questions = len(test_session.questions_order) if test_session.questions_order else 0
        
        logger.info(f"Test completion: {answered_count}/{total_questions} questions answered")
        
        questions = await self.test_generator.get_questions_by_ids(test_session.questions_order)
        
        scoring_result = await self.scoring_service.calculate_total_score(
            questions, user_answers
        )
        
        logger.info(
            f"Test scored: {scoring_result['percentage']}% - "
            f"{'PASSED' if scoring_result['passed'] else 'FAILED'}"
        )
        
        test_result = TestResult(
            session_id=test_session.id,
            keycloak_id=keycloak_id,
            total_score=scoring_result["total_score"],
            max_possible_score=scoring_result["max_possible_score"],
            percentage=scoring_result["percentage"],
            passed=scoring_result["passed"]
        )
        
        self.db.add(test_result)
        test_session.status = TestStatus.COMPLETED
        test_session.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(test_session)
        await self.db.refresh(test_result)
        
        # Публикуем событие о завершении теста
        try:
            await self.event_service.publish_test_completed(
                keycloak_id=keycloak_id,
                session_id=str(session_id),
                results={
                    "total_score": test_result.total_score,
                    "percentage": test_result.percentage,
                    "passed": test_result.passed
                }
            )
            logger.info(f"Test completion event published for {keycloak_id}")
        except Exception as e:
            logger.error(f"Failed to publish test completion event: {e}")
        
        logger.info(f"Test completed for user {keycloak_id}: session {session_id}")
        
        return await self._format_results(test_session, test_result)
    
    async def get_test_results(
        self,
        session_id: uuid.UUID,
        keycloak_id: str
    ) -> Dict[str, Any]:
        """Получение результатов теста"""
        
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
                history.append({
                    "session_id": str(session.id),
                    "test_name": "Dating Readiness Test",
                    "completed_at": session.completed_at.isoformat(),
                    "total_score": session.result.total_score,
                    "percentage": session.result.percentage,
                    "passed": session.result.passed
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
        
        query = select(TestSession).options(
            selectinload(TestSession.result)
        ).where(
            TestSession.keycloak_id == keycloak_id,
            TestSession.status == TestStatus.COMPLETED
        )
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        total_tests_taken = len(sessions)
        total_tests_completed = len(sessions)
        
        if total_tests_completed > 0:
            total_percentage = sum(
                session.result.percentage for session in sessions if session.result
            )
            average_score = round(total_percentage / total_tests_completed, 2)
            
            last_test_date = max(
                (session.completed_at for session in sessions if session.completed_at),
                default=None
            )
        else:
            average_score = 0.0
            last_test_date = None
        
        return {
            "total_tests_taken": total_tests_taken,
            "total_tests_completed": total_tests_completed,
            "average_score": average_score,
            "last_test_date": last_test_date.isoformat() if last_test_date else None
        }
    
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
    
    async def _format_results(
        self,
        test_session: TestSession,
        test_result: TestResult
    ) -> Dict[str, Any]:
        """Форматирование результатов для ответа"""
        return {
            "session_id": str(test_session.id),
            "status": test_session.status.value if isinstance(
                test_session.status, TestStatus
            ) else str(test_session.status),
            "completed_at": test_session.completed_at.isoformat(),
            "time_spent_minutes": (
                (test_session.completed_at - test_session.started_at).total_seconds() / 60
                if test_session.completed_at and test_session.started_at else None
            ),
            "results": {
                "total_score": test_result.total_score,
                "max_possible_score": test_result.max_possible_score,
                "percentage": test_result.percentage,
                "passed": test_result.passed
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
        if not test_session.result:
            await self.db.refresh(test_session, ['result'])
        
        return await self._format_results(test_session, test_session.result)
    
    async def _calculate_and_save_results(self, test_session: TestSession) -> Dict[str, Any]:
        """Пересчет и сохранение результатов (если результат потерян)"""
        raise DatabaseException("Test results need to be recalculated")