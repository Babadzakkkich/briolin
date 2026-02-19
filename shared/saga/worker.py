import asyncio
import json
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable, List
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from shared.rabbitmq.publisher import RabbitMQPublisher
from shared.events.schemas import BaseEvent, EventType
from .models import SagaOutbox, SagaInstance, SagaStatus
from .exceptions import SagaStepFailedException

class SagaWorker:
    """
    Фоновый воркер для обработки SAGA событий из outbox таблицы.
    Запускается в каждом сервисе как отдельная asyncio задача.
    """
    
    def __init__(
        self,
        db_url: str,
        publisher: RabbitMQPublisher,
        service_name: str,
        poll_interval: int = 1,
        batch_size: int = 100
    ):
        self.db_url = db_url
        self.publisher = publisher
        self.service_name = service_name
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._step_handlers: Dict[str, Callable] = {}
    
    def register_step_handler(self, step_name: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """Регистрирует обработчик для шага саги"""
        self._step_handlers[step_name] = handler
    
    async def start(self):
        """Запускает воркер"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        print(f"SAGA Worker for {self.service_name} started")
    
    async def stop(self):
        """Останавливает воркер"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.engine.dispose()
        print(f"SAGA Worker for {self.service_name} stopped")
    
    async def _run(self):
        """Основной цикл воркера"""
        while self._running:
            try:
                await self._process_outbox()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"Error in SAGA worker: {e}")
                await asyncio.sleep(5)
    
    async def _get_step_result(self, session: AsyncSession, saga_id: str, step_name: str) -> Dict[str, Any]:
        """Получает результат выполненного шага"""
        stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance and instance.step_results:
            return instance.step_results.get(step_name, {})
        return {}
    
    async def _are_dependencies_satisfied(self, session: AsyncSession, message: SagaOutbox) -> bool:
        """Проверяет, выполнены ли все зависимости для сообщения"""
        depends_on = message.headers.get("depends_on")
        if not depends_on:
            return True
        
        # Поддерживаем как строку, так и список зависимостей
        dependencies = [depends_on] if isinstance(depends_on, str) else depends_on
        
        for dep in dependencies:
            # Проверяем, есть ли выполненный шаг с таким именем
            stmt = select(SagaOutbox).where(
                and_(
                    SagaOutbox.saga_id == message.saga_id,
                    SagaOutbox.step_name == dep,
                    SagaOutbox.status == SagaStatus.COMPLETED
                )
            )
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                # Также проверяем в step_results
                step_result = await self._get_step_result(session, message.saga_id, dep)
                if not step_result:
                    return False
        
        return True
    
    async def _process_outbox(self):
        """Обрабатывает сообщения из outbox"""
        async with self.async_session() as session:
            # Получаем pending сообщения
            stmt = (
                select(SagaOutbox)
                .where(
                    and_(
                        SagaOutbox.status == SagaStatus.PENDING,
                        SagaOutbox.attempts < SagaOutbox.max_attempts
                    )
                )
                .order_by(SagaOutbox.created_at)
                .limit(self.batch_size)
                .with_for_update(skip_locked=True)
            )
            result = await session.execute(stmt)
            all_messages = result.scalars().all()
            
            # Фильтруем сообщения по зависимостям
            messages_to_process = []
            for message in all_messages:
                if await self._are_dependencies_satisfied(session, message):
                    messages_to_process.append(message)
                else:
                    # Если зависимости не выполнены, пропускаем (будет picked up позже)
                    continue
            
            for message in messages_to_process:
                await self._process_message(session, message)
            
            await session.commit()
    
    async def _process_message(self, session: AsyncSession, message: SagaOutbox):
        """Обрабатывает одно сообщение"""
        try:
            # Помечаем как processing
            message.status = SagaStatus.PROCESSING
            message.attempts += 1
            await session.flush()
            
            # Получаем обработчик для этого шага
            handler = self._step_handlers.get(message.step_name)
            if not handler:
                raise ValueError(f"No handler registered for step: {message.step_name}")
            
            # Получаем результаты зависимых шагов
            context = {}
            depends_on = message.headers.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                step_result = await self._get_step_result(session, message.saga_id, dep)
                if step_result:
                    context[dep] = step_result
            
            # Выполняем обработчик
            result = await handler({
                "saga_id": message.saga_id,
                "step_name": message.step_name,
                "payload": message.payload,
                "headers": message.headers,
                "context": context  # Передаем контекст с результатами предыдущих шагов
            })
            
            # Помечаем как выполненное
            message.status = SagaStatus.COMPLETED
            message.processed_at = datetime.utcnow()
            
            # Обновляем экземпляр саги с результатом
            await self._update_saga_instance(session, message.saga_id, message.step_name, result)
            
        except Exception as e:
            error_msg = str(e)
            message.last_error = error_msg
            message.status = SagaStatus.FAILED
            
            print(f"Failed to process saga message {message.id}: {error_msg}")
            
            # Если превышено кол-во попыток, запускаем компенсацию
            if message.attempts >= message.max_attempts:
                await self._initiate_compensation(session, message.saga_id, error_msg)
    
    async def _update_saga_instance(self, session: AsyncSession, saga_id: str, step_name: str, result: Dict[str, Any]):
        """Обновляет экземпляр саги с результатом шага"""
        stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
        result_saga = await session.execute(stmt)
        instance = result_saga.scalar_one_or_none()
        
        if not instance:
            # Создаем новый экземпляр если не существует
            instance = SagaInstance(
                saga_id=saga_id,
                saga_name=step_name.split('_')[0] if '_' in step_name else step_name,
                context={},
                step_results={step_name: result}
            )
            session.add(instance)
        else:
            step_results = instance.step_results or {}
            step_results[step_name] = result
            instance.step_results = step_results
            
            # Проверяем, все ли шаги выполнены
            await self._check_saga_completion(session, instance)
        
        await session.flush()
    
    async def _check_saga_completion(self, session: AsyncSession, instance: SagaInstance):
        """Проверяет, завершена ли сага (все шаги выполнены)"""
        # Получаем все шаги для этой саги
        stmt = select(SagaOutbox).where(
            and_(
                SagaOutbox.saga_id == instance.saga_id,
                SagaOutbox.step_name.notlike("compensate_%")  # Исключаем компенсации
            )
        )
        result = await session.execute(stmt)
        all_steps = result.scalars().all()
        
        # Проверяем, все ли шаги завершены
        all_completed = all(
            step.status == SagaStatus.COMPLETED 
            for step in all_steps
        )
        
        if all_completed:
            instance.status = SagaStatus.COMPLETED
            instance.completed_at = datetime.utcnow()
    
    async def _initiate_compensation(self, session: AsyncSession, saga_id: str, error: str):
        """Инициирует компенсацию для саги"""
        # Находим все выполненные шаги этой саги (не компенсации)
        stmt = (
            select(SagaOutbox)
            .where(
                and_(
                    SagaOutbox.saga_id == saga_id,
                    SagaOutbox.status == SagaStatus.COMPLETED,
                    SagaOutbox.step_name.notlike("compensate_%")
                )
            )
            .order_by(SagaOutbox.created_at.desc())
        )
        result = await session.execute(stmt)
        completed_steps = result.scalars().all()
        
        # Создаем компенсирующие события в обратном порядке
        for step in completed_steps:
            # Проверяем, не создали ли уже компенсацию
            check_stmt = select(SagaOutbox).where(
                and_(
                    SagaOutbox.saga_id == saga_id,
                    SagaOutbox.step_name == f"compensate_{step.step_name}"
                )
            )
            check_result = await session.execute(check_stmt)
            if check_result.scalar_one_or_none():
                continue  # Компенсация уже создана
            
            compensation_event = SagaOutbox(
                saga_id=saga_id,
                saga_name=step.saga_name,
                step_name=f"compensate_{step.step_name}",
                status=SagaStatus.PENDING,
                event_type=f"compensate.{step.event_type}",
                payload=step.payload,
                headers={
                    **step.headers, 
                    "original_step": step.step_name, 
                    "error": error,
                    "compensation_for": step.step_name
                }
            )
            session.add(compensation_event)
        
        # Обновляем статус саги
        update_stmt = (
            update(SagaInstance)
            .where(SagaInstance.saga_id == saga_id)
            .values(
                status=SagaStatus.COMPENSATING,
                error=error,
                updated_at=datetime.utcnow()
            )
        )
        await session.execute(update_stmt)

    async def create_saga_outbox(
        self,
        saga_id: str,
        saga_name: str,
        step_name: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, Any] = None
    ) -> str:
        """Создает запись в outbox (вызывается из бизнес-логики)"""
        
        # Функция для сериализации специальных типов
        def json_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif hasattr(obj, 'value'):  # для Enum
                return obj.value
            elif isinstance(obj, (set, frozenset)):
                return list(obj)
            raise TypeError(f"Type {type(obj)} not serializable")
        
        async with self.async_session() as session:
            # Сериализуем payload и headers в JSON-совместимый формат
            serialized_payload = json.loads(
                json.dumps(payload, default=json_serializer)
            )
            serialized_headers = json.loads(
                json.dumps(headers or {}, default=json_serializer)
            )
            
            outbox = SagaOutbox(
                saga_id=saga_id,
                saga_name=saga_name,
                step_name=step_name,
                status=SagaStatus.PENDING,
                event_type=event_type,
                payload=serialized_payload,  # Используем сериализованные данные
                headers=serialized_headers
            )
            session.add(outbox)
            
            # Также создаем или обновляем экземпляр саги
            stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                instance = SagaInstance(
                    saga_id=saga_id,
                    saga_name=saga_name,
                    context=payload.get("context", {}),
                    status=SagaStatus.PENDING
                )
                session.add(instance)
            
            await session.commit()
            return saga_id
    
    async def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """Получает статус саги (для API)"""
        async with self.async_session() as session:
            stmt = select(SagaInstance).where(SagaInstance.saga_id == saga_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                return None
            
            # Получаем все шаги
            steps_stmt = select(SagaOutbox).where(SagaOutbox.saga_id == saga_id)
            steps_result = await session.execute(steps_stmt)
            steps = steps_result.scalars().all()
            
            return {
                "saga_id": instance.saga_id,
                "name": instance.saga_name,
                "status": instance.status,
                "created_at": instance.created_at.isoformat() if instance.created_at else None,
                "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
                "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                "error": instance.error,
                "steps": [
                    {
                        "name": step.step_name,
                        "status": step.status,
                        "attempts": step.attempts,
                        "error": step.last_error,
                        "created_at": step.created_at.isoformat() if step.created_at else None
                    }
                    for step in steps
                ],
                "step_results": instance.step_results
            }