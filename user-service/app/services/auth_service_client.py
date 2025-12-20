import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logger import logger

class AuthServiceClient:
    """Клиент для взаимодействия с auth-service (для синхронизации пользователей)"""
    
    def __init__(self):
        # Получаем URL из настроек (нужно добавить в config)
        self.auth_service_url = settings.auth_service_url
        self.timeout = httpx.Timeout(30.0)
    
    async def update_user_in_auth_service(self, keycloak_id: str, update_data: dict) -> bool:
        """Обновление пользователя в auth-service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.auth_service_url}/api/v1/internal/users/{keycloak_id}",
                    json=update_data,
                    headers={"x-internal-request": "true"}
                )
                
                if response.status_code == 200:
                    logger.info(f"User {keycloak_id} updated in auth-service")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"User {keycloak_id} not found in auth-service")
                    return False
                else:
                    logger.error(f"Auth-service update error: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to update user in auth-service: {response.text}")
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to auth-service at {self.auth_service_url}")
            raise Exception("Auth service unavailable")
        except Exception as e:
            logger.error(f"Error updating user in auth-service: {e}")
            raise
    
    async def delete_user_from_auth_service(self, keycloak_id: str) -> bool:
        """Удаление пользователя из auth-service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.auth_service_url}/api/v1/internal/users/{keycloak_id}",
                    headers={"x-internal-request": "true"}
                )
                
                if response.status_code == 200:
                    logger.info(f"User {keycloak_id} deleted from auth-service")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"User {keycloak_id} not found in auth-service")
                    return True  # Если пользователя нет, считаем удаление успешным
                else:
                    logger.error(f"Auth-service delete error: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to delete user from auth-service: {response.text}")
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to auth-service at {self.auth_service_url}")
            raise Exception("Auth service unavailable")
        except Exception as e:
            logger.error(f"Error deleting user from auth-service: {e}")
            raise

# Singleton экземпляр
_auth_service_client = None

def get_auth_service_client() -> AuthServiceClient:
    global _auth_service_client
    if _auth_service_client is None:
        _auth_service_client = AuthServiceClient()
    return _auth_service_client