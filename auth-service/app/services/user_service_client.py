import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logger import logger

class UserServiceClient:
    def __init__(self):
        self.base_url = settings.user_service.url
        self.timeout = httpx.Timeout(30.0)
    
    async def create_user_profile(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        role: str
    ) -> None:
        """Создание расширенного профиля в user-service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/users",  # ДОБАВЛЕН /api/v1/
                json={
                    "keycloak_id": keycloak_id,
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role
                },
                headers={"x-internal-request": "true"}
            )
            
            if response.status_code != 201:
                logger.error(f"User-service returned {response.status_code}: {response.text}")
                raise Exception(f"Failed to create user profile in user-service")
    
    async def get_user_profile(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение расширенного профиля из user-service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/internal/users/{keycloak_id}",  # ДОБАВЛЕН /api/v1/
                headers={"x-internal-request": "true"}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"User-service error: {response.status_code}")
                raise Exception(f"User-service error: {response.status_code}")
    
    async def delete_user_profile(self, keycloak_id: str) -> None:
        """Удаление профиля из user-service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/internal/users/{keycloak_id}",  # ДОБАВЛЕН /api/v1/
                headers={"x-internal-request": "true"}
            )
            
            if response.status_code not in [200, 204, 404]:
                logger.error(f"User-service delete error: {response.status_code}")
                raise Exception(f"Failed to delete user profile from user-service")

user_service_client = UserServiceClient()