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

_keycloak_client = None

def get_keycloak_client() -> KeycloakClient:
    global _keycloak_client
    if _keycloak_client is None:
        _keycloak_client = KeycloakClient()
    return _keycloak_client

def get_profile_service(
    kc_client: KeycloakClient = Depends(get_keycloak_client)
) -> ProfileService:
    return ProfileService(kc_client)

__all__ = [
    'get_keycloak_client',
    'get_profile_service',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role',
    'require_test_passed'
]