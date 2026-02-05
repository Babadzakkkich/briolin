import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logger import logger


class UserServiceClient:
    """Клиент для взаимодействия с user-service"""
    
    def __init__(self):
        self.base_url = settings.user_service.url
        self.timeout = httpx.Timeout(5.0)
    
    async def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по keycloak_id"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/internal/users/{keycloak_id}",
                    headers={"x-internal-request": "true"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"User {keycloak_id} not found in user-service")
                    return None
                else:
                    logger.error(f"Unexpected response from user-service: {response.status_code}")
                    return None
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to user-service at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching user from user-service: {e}")
            return None


# Глобальный экземпляр
_user_service_client = None

def get_user_service_client() -> UserServiceClient:
    global _user_service_client
    if _user_service_client is None:
        _user_service_client = UserServiceClient()
    return _user_service_client