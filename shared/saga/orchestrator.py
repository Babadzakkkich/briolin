import uuid
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from shared.saga.exceptions import SagaStepFailedException

logger = logging.getLogger("briolin.saga")

class SagaStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"

@dataclass
class SagaStep:
    name: str
    service: str
    action: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    compensation: Optional[Callable[[Dict[str, Any]], Awaitable[bool]]] = None
    retry_count: int = 3
    retry_delay: int = 1
    timeout: int = 30

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Executing SAGA step '{self.name}' (attempt {attempt + 1}/{self.retry_count})")
                result = await asyncio.wait_for(self.action(context), timeout=self.timeout)
                logger.info(f"SAGA step '{self.name}' executed successfully")
                return result
            except asyncio.TimeoutError:
                logger.error(f"SAGA step '{self.name}' timed out (attempt {attempt + 1})")
                if attempt == self.retry_count - 1:
                    raise SagaStepFailedException(f"Step '{self.name}' timed out after {self.retry_count} attempts")
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"SAGA step '{self.name}' failed (attempt {attempt + 1}): {e}")
                if attempt == self.retry_count - 1:
                    raise SagaStepFailedException(f"Step '{self.name}' failed: {str(e)}")
                await asyncio.sleep(self.retry_delay)
        raise SagaStepFailedException(f"Step '{self.name}' failed after {self.retry_count} attempts")

    async def compensate(self, context: Dict[str, Any]) -> bool:
        if not self.compensation:
            logger.warning(f"No compensation defined for SAGA step '{self.name}'")
            return True
        try:
            logger.info(f"Compensating SAGA step '{self.name}'")
            success = await self.compensation(context)
            if success:
                logger.info(f"SAGA step '{self.name}' compensated successfully")
            else:
                logger.error(f"SAGA step '{self.name}' compensation failed")
            return success
        except Exception as e:
            logger.error(f"Error during compensation of SAGA step '{self.name}': {e}")
            return False

class SagaOrchestrator:
    def __init__(self):
        self.sagas: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def start_saga(
        self,
        name: str,
        steps: List[SagaStep],
        initial_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        saga_id = str(uuid.uuid4())
        saga = {
            "id": saga_id,
            "name": name,
            "status": SagaStatus.PENDING,
            "steps": steps,
            "current_step": 0,
            "context": initial_context or {},
            "results": {},
            "compensation_results": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error": None
        }
        async with self._lock:
            self.sagas[saga_id] = saga
        logger.info(f"Started SAGA '{name}' with ID: {saga_id}")
        asyncio.create_task(self._execute_saga(saga_id))
        return {
            "saga_id": saga_id,
            "status": SagaStatus.PENDING,
            "created_at": saga["created_at"]
        }

    async def _execute_saga(self, saga_id: str):
        async with self._lock:
            saga = self.sagas.get(saga_id)
            if not saga:
                return
        try:
            saga["status"] = SagaStatus.IN_PROGRESS
            saga["updated_at"] = datetime.utcnow().isoformat()
            steps = saga["steps"]
            context = saga["context"]
            results = saga["results"]
            for i, step in enumerate(steps):
                saga["current_step"] = i
                saga["updated_at"] = datetime.utcnow().isoformat()
                logger.info(f"SAGA {saga_id}: Executing step {i+1}/{len(steps)}: {step.name}")
                try:
                    step_result = await step.execute(context)
                    results[step.name] = {
                        "status": "completed",
                        "result": step_result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    context.update(step_result.get("saga_context", {}))
                except SagaStepFailedException as e:
                    saga["error"] = str(e)
                    saga["status"] = SagaStatus.FAILED
                    saga["updated_at"] = datetime.utcnow().isoformat()
                    logger.error(f"SAGA {saga_id} failed at step {step.name}: {e}")
                    await self._compensate_saga(saga_id, i)
                    return
            saga["status"] = SagaStatus.COMPLETED
            saga["updated_at"] = datetime.utcnow().isoformat()
            logger.info(f"SAGA {saga_id} completed successfully")
        except Exception as e:
            logger.error(f"Unexpected error in SAGA {saga_id}: {e}")
            saga["error"] = str(e)
            saga["status"] = SagaStatus.FAILED
            saga["updated_at"] = datetime.utcnow().isoformat()

    async def _compensate_saga(self, saga_id: str, failed_step_index: int):
        async with self._lock:
            saga = self.sagas.get(saga_id)
            if not saga:
                return
        saga["status"] = SagaStatus.COMPENSATING
        saga["updated_at"] = datetime.utcnow().isoformat()
        steps = saga["steps"][:failed_step_index]
        context = saga["context"]
        compensation_results = saga["compensation_results"]
        for i in range(len(steps) - 1, -1, -1):
            step = steps[i]
            logger.info(f"SAGA {saga_id}: Compensating step {step.name}")
            try:
                success = await step.compensate(context)
                compensation_results[step.name] = {
                    "status": "compensated" if success else "failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                if not success:
                    logger.warning(f"SAGA {saga_id}: Step {step.name} compensation failed")
            except Exception as e:
                logger.error(f"SAGA {saga_id}: Error compensating step {step.name}: {e}")
                compensation_results[step.name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        saga["status"] = SagaStatus.COMPENSATED
        saga["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"SAGA {saga_id} compensated")

    async def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            saga = self.sagas.get(saga_id)
        if not saga:
            return None
        return {
            "saga_id": saga_id,
            "name": saga["name"],
            "status": saga["status"],
            "current_step": saga["current_step"],
            "total_steps": len(saga["steps"]),
            "error": saga["error"],
            "created_at": saga["created_at"],
            "updated_at": saga["updated_at"],
            "results": saga.get("results", {}),
            "compensation_results": saga.get("compensation_results", {})
        }

_saga_orchestrator = None

def get_saga_orchestrator() -> SagaOrchestrator:
    global _saga_orchestrator
    if _saga_orchestrator is None:
        _saga_orchestrator = SagaOrchestrator()
    return _saga_orchestrator