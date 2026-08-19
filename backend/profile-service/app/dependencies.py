from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_any_role,
    require_test_passed
)
from app.database.session import async_session_factory
from app.services.keycloak_client import KeycloakClient
from app.services.profile_service import ProfileService
from app.services.saga_worker import get_saga_worker

_keycloak_client = None

def get_keycloak_client() -> KeycloakClient:
    global _keycloak_client
    if _keycloak_client is None:
        _keycloak_client = KeycloakClient()
    return _keycloak_client

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_profile_service(
    db: AsyncSession = Depends(get_db),
    kc_client: KeycloakClient = Depends(get_keycloak_client)
) -> ProfileService:
    return ProfileService(db, kc_client) 

__all__ = [
    'get_db'
    'get_keycloak_client',
    'get_profile_service',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role',
    'require_test_passed',
    'get_saga_worker'
]