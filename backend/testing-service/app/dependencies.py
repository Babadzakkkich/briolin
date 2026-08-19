from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import get_current_user, get_current_active_user, require_role, require_any_role
from app.database.session import async_session_factory
from app.services.testing_service import TestingService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_testing_service(
    db: AsyncSession = Depends(get_db)
) -> TestingService:
    return TestingService(db)

# Экспортируем shared зависимости
__all__ = [
    'get_db',
    'get_testing_service',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role'
]