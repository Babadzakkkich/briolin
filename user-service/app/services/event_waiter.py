import asyncio
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from app.core.logger import logger

class EventWaiter:
    """Класс для ожидания подтверждения событий между сервисами"""
    
    def __init__(self):
        self._waiters: Dict[str, asyncio.Event] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def wait_for_event(
        self, 
        correlation_id: str,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Ожидание события с указанным correlation_id"""
        # Создаем event для этого correlation_id
        async with self._lock:
            if correlation_id not in self._waiters:
                self._waiters[correlation_id] = asyncio.Event()
        
        waiter = self._waiters[correlation_id]
        
        try:
            # Ждем события с таймаутом
            await asyncio.wait_for(waiter.wait(), timeout=timeout)
            
            # Возвращаем результат
            async with self._lock:
                result = self._results.get(correlation_id)
                return result
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for event with correlation_id: {correlation_id}")
            return None
        finally:
            # Очищаем ресурсы
            async with self._lock:
                if correlation_id in self._waiters:
                    del self._waiters[correlation_id]
                if correlation_id in self._results:
                    del self._results[correlation_id]
    
    async def set_event_result(
        self, 
        correlation_id: str, 
        result: Dict[str, Any]
    ) -> bool:
        """Установка результата для ожидающего события"""
        async with self._lock:
            if correlation_id in self._waiters:
                self._results[correlation_id] = result
                self._waiters[correlation_id].set()
                logger.debug(f"Event result set for correlation_id: {correlation_id}")
                return True
            else:
                logger.debug(f"No waiter found for correlation_id: {correlation_id}")
                return False
    
    def has_waiter(self, correlation_id: str) -> bool:
        """Проверка, есть ли ожидающий для этого correlation_id"""
        return correlation_id in self._waiters
    
    async def cleanup_old_waiters(self, max_age_seconds: int = 300):
        """Очистка старых ожидающих (запускается периодически)"""
        async with self._lock:
            current_time = datetime.now()
            to_remove = []
            
            for corr_id, waiter in list(self._waiters.items()):
                # В реальной системе здесь можно отслеживать время создания
                # Для простоты удаляем только если событие уже произошло
                if waiter.is_set() and corr_id in self._results:
                    result = self._results[corr_id]
                    # Проверяем время в результате, если есть
                    if 'timestamp' in result:
                        result_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                        if current_time - result_time > timedelta(seconds=max_age_seconds):
                            to_remove.append(corr_id)
            
            for corr_id in to_remove:
                del self._waiters[corr_id]
                if corr_id in self._results:
                    del self._results[corr_id]
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old event waiters")

# Глобальный экземпляр
_event_waiter = None

def get_event_waiter() -> EventWaiter:
    global _event_waiter
    if _event_waiter is None:
        _event_waiter = EventWaiter()
    return _event_waiter