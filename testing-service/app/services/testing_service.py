import uuid
import json
import aio_pika
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
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
        self._email_channel = None
        self._email_connection = None
    
    # ========== ОТПРАВКА EMAIL ==========
    
    async def _send_email_notification(self, email_type: str, to_email: str, **kwargs):
        """Отправить уведомление в email-сервис через RabbitMQ"""
        try:
            if not self._email_channel:
                connection = await aio_pika.connect_robust(
                    f"amqp://{settings.rabbitmq.user}:{settings.rabbitmq.password}@{settings.rabbitmq.host}:{settings.rabbitmq.port}/"
                )
                self._email_channel = await connection.channel()
                await self._email_channel.declare_queue("email.notifications", durable=True)
                self._email_connection = connection
            
            message = {
                "type": email_type,
                "to": to_email,
                **kwargs
            }
            
            await self._email_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="email.notifications"
            )
            logger.info(f"Email notification queued: {email_type} -> {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to queue email notification: {e}")
    
    async def send_test_results_email(self, email: str, name: str, test_name: str, score: int, total: int):
        """Отправить письмо с результатами теста"""
        percentage = round((score / total) * 100, 1) if total > 0 else 0
        
        await self._send_email_notification(
            "test_complete",
            email,
            name=name,
            test_name=test_name,
            score=score,
            total=total,
            percentage=percentage
        )
    
    async def _get_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе из auth-service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://auth-service:8001/api/v1/users/{keycloak_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "email": user_data.get("email"),
                        "name": user_data.get("username", "User"),
                        "keycloak_id": keycloak_id
                    }
                else:
                    logger.warning(f"Auth-service returned {response.status_code} for user {keycloak_id}")
        except httpx.TimeoutException:
            logger.error(f"Timeout getting user info for {keycloak_id}")
        except httpx.ConnectError:
            logger.error(f"Connection error to auth-service for user {keycloak_id}")
        except Exception as e:
            logger.error(f"Failed to get user info from auth-service: {e}")
        
        # Fallback на заглушку
        logger.warning(f"Using fallback email for user {keycloak_id}")
        return {
            "email": f"user_{keycloak_id[:8]}@example.com",
            "name": "User"
        }
    
    # ========== ОСНОВНЫЕ МЕТОДЫ ==========
    
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
        
        logger.info(f"Test session started for user {keycloak_id}: {test_session.id}")
        
        # Формируем вопросы для отправки клиенту (без баллов)
        questions_for_client = []
        for question in questions:
            question_dict = question.dict()
            
            if "options" in question_dict:
                for option in question_dict["options"]:
                    if "score" in option:
                        del option["score"]
                    if "is_correct" in option:
                        del option["is_correct"]
            
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
        keycloak_id: str,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
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
        
        # ========== ОТПРАВКА EMAIL С РЕЗУЛЬТАТАМИ ТЕСТА ==========
        try:
            # Сначала пытаемся использовать email из токена
            if user_email:
                await self.send_test_results_email(
                    email=user_email,
                    name=user_name or "User",
                    test_name="Dating Readiness Test",
                    score=test_result.total_score,
                    total=test_result.max_possible_score
                )
                logger.info(f"Test results email sent to {user_email} from token")
            else:
                # Если в токене нет email, делаем запрос к auth-service
                user_info = await self._get_user_info(keycloak_id)
                if user_info and user_info.get("email"):
                    await self.send_test_results_email(
                        email=user_info["email"],
                        name=user_info.get("name", "User"),
                        test_name="Dating Readiness Test",
                        score=test_result.total_score,
                        total=test_result.max_possible_score
                    )
                    logger.info(f"Test results email sent to {user_info['email']} from auth-service")
                else:
                    logger.warning(f"No email found for user {keycloak_id}, skipping email")
        except Exception as e:
            logger.error(f"Failed to send test results email: {e}")
        # =========================================================
        
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
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
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