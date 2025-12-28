import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger("briolin.saga.compensation")

class CompensationAction:
    def __init__(
        self,
        service: str,
        action: Callable[[Dict[str, Any]], Awaitable[bool]],
        description: str = ""
    ):
        self.service = service
        self.action = action
        self.description = description

    async def execute(self, context: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Executing compensation action: {self.description}")
            result = await self.action(context)
            if result:
                logger.info(f"Compensation action completed: {self.description}")
            else:
                logger.error(f"Compensation action failed: {self.description}")
            return result
        except Exception as e:
            logger.error(f"Error executing compensation action {self.description}: {e}")
            return False

class CompensationRegistry:
    def __init__(self):
        self.actions: Dict[str, CompensationAction] = {}

    def register(
        self,
        name: str,
        service: str,
        action: Callable[[Dict[str, Any]], Awaitable[bool]],
        description: str = ""
    ):
        self.actions[name] = CompensationAction(
            service=service,
            action=action,
            description=description
        )
        logger.info(f"Registered compensation action: {name} for service {service}")

    def get(self, name: str):
        return self.actions.get(name)

_compensation_registry = None

def get_compensation_registry() -> CompensationRegistry:
    global _compensation_registry
    if _compensation_registry is None:
        _compensation_registry = CompensationRegistry()
    return _compensation_registry