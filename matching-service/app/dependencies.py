from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory
from app.services.matching_service import MatchingService
from shared.auth.dependencies import get_current_user, get_current_active_user, require_role, require_any_role, require_test_passed


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_matching_service(db: AsyncSession = Depends(get_db)) -> MatchingService:
    return MatchingService(db)


# Re-export shared dependencies
__all__ = [
    'get_db',
    'get_matching_service',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role',
    'require_test_passed',
    'require_admin'
]


def require_admin():
    return require_role("admin")