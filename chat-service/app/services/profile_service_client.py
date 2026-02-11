import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logger import logger


class ProfileServiceClient:
    """Клиент для взаимодействия с profile-service"""
    
    def __init__(self):
        self.base_url = settings.profile_service_url
        self.timeout = httpx.Timeout(5.0)
    
    async def get_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение полного профиля пользователя по keycloak_id"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/internal/profiles/{keycloak_id}",
                    headers={"x-internal-request": "true"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Profile not found for user {keycloak_id}")
                    return None
                else:
                    logger.error(f"Unexpected response from profile-service: {response.status_code}")
                    return None
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to profile-service at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching profile from profile-service: {e}")
            return None
    
    async def get_basic_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Получение базового профиля пользователя по keycloak_id (легковесный запрос)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/internal/profiles/{keycloak_id}/basic",
                    headers={"x-internal-request": "true"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Basic profile not found for user {keycloak_id}")
                    return None
                else:
                    logger.error(f"Unexpected response from profile-service: {response.status_code}")
                    return None
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to profile-service at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching basic profile from profile-service: {e}")
            return None
    
    async def get_display_name(self, keycloak_id: str) -> str:
        """Получение отображаемого имени пользователя (first_name + last_name)"""
        profile = await self.get_basic_profile_by_keycloak_id(keycloak_id)
        
        if profile:
            first_name = profile.get("first_name", "")
            last_name = profile.get("last_name", "")
            
            if first_name and last_name:
                return f"{first_name} {last_name}".strip()
            elif first_name:
                return first_name
            elif last_name:
                return last_name
        
        # Fallback на keycloak_id если профиль не найден
        logger.warning(f"Using fallback for display name: {keycloak_id[:8]}...")
        return keycloak_id[:8]
    
    async def get_avatar_url(self, keycloak_id: str) -> Optional[str]:
        """Получение URL аватарки пользователя"""
        profile = await self.get_profile_by_keycloak_id(keycloak_id)
        
        if profile and "basic" in profile:
            # Предполагаем, что аватарка хранится в basic профиле
            # Можно расширить модель BasicProfile в profile-service
            return profile["basic"].get("avatar_url")
        
        return None


# Глобальный экземпляр
_profile_service_client = None

def get_profile_service_client() -> ProfileServiceClient:
    global _profile_service_client
    if _profile_service_client is None:
        _profile_service_client = ProfileServiceClient()
    return _profile_service_client