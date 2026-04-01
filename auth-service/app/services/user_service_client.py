import httpx
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import UserAlreadyExistsException, ValidationException, DatabaseException


class UserServiceClient:
    """Клиент для синхронного взаимодействия с user-service"""
    
    def __init__(self):
        self.base_url = settings.user_service.url
        self.timeout = httpx.Timeout(30.0)
    
    async def create_user_profile(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        role: str,
        correlation_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Синхронное создание профиля пользователя в user-service
        
        Returns:
            Dict с данными созданного пользователя или None при ошибке
        """
        url = urljoin(self.base_url.rstrip("/") + "/", "api/v1/internal/users")
        
        payload = {
            "keycloak_id": keycloak_id,
            "email": email,
            "username": username,
            "role": role
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Request": "true"
        }
        
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 201:
                    user_data = response.json()
                    logger.info(f"User profile created in user-service: {keycloak_id}")
                    return user_data
                elif response.status_code == 409:
                    error_data = response.json()
                    logger.warning(f"User already exists: {error_data.get('detail')}")
                    raise UserAlreadyExistsException(error_data.get("detail", "User already exists"))
                elif response.status_code == 400:
                    error_data = response.json()
                    logger.error(f"Validation error from user-service: {error_data}")
                    raise ValidationException(error_data.get("detail", "Validation error"))
                else:
                    logger.error(f"Unexpected response from user-service: {response.status_code}")
                    return None
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to user-service at {self.base_url}")
            raise DatabaseException("User service unavailable")
        except UserAlreadyExistsException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error creating user profile in user-service: {e}")
            raise DatabaseException(f"Failed to create user profile: {str(e)}")


# Глобальный экземпляр
_user_service_client = None


def get_user_service_client() -> UserServiceClient:
    """Получение экземпляра UserServiceClient (синглтон)"""
    global _user_service_client
    if _user_service_client is None:
        _user_service_client = UserServiceClient()
    return _user_service_client