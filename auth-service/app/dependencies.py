from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import get_current_user, get_current_active_user, require_role, require_any_role
from app.database.session import async_session_factory
from app.services.keycloak_client import KeycloakClient
from app.services.auth_service import AuthService
from app.services.user_service import UserService


# Singleton для Keycloak клиента
_keycloak_client = KeycloakClient()

def get_keycloak_client() -> KeycloakClient:
    return _keycloak_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    kc_client: KeycloakClient = Depends(get_keycloak_client)
) -> AuthService:
    return AuthService(db, kc_client)


def get_user_service(
    db: AsyncSession = Depends(get_db),
    kc_client: KeycloakClient = Depends(get_keycloak_client)
) -> UserService:
    return UserService(db, kc_client)


# Экспортируем shared зависимости
__all__ = [
    'get_db',
    'get_keycloak_client',
    'get_auth_service',
    'get_user_service',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_any_role'
]