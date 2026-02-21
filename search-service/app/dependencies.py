from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import session_factory
from app.services.profile_service_client import get_profile_client, ProfileServiceClient
from app.services.search import SearchService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session
    """
    async with session_factory() as session:
        yield session


def get_profile_client_dep() -> ProfileServiceClient:
    """
    Dependency for getting profile service client
    """
    return get_profile_client()


def get_search_service(
    db: AsyncSession = Depends(get_db),
    profile_client: ProfileServiceClient = Depends(get_profile_client_dep)
) -> SearchService:
    """
    Dependency for getting search service instance
    """
    return SearchService(db, profile_client)


__all__ = [
    'get_db',
    'get_profile_client_dep',
    'get_search_service',
    'get_current_user',  # эти импортируются из shared
    'get_current_active_user',
    'require_role',
    'require_any_role',
    'require_test_passed',
]