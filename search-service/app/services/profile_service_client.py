import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import SearchServiceException


class ProfileServiceClient:
    """
    Клиент для взаимодействия с profile-service через внутренние эндпоинты
    """

    def __init__(self):
        self.base_url = settings.profile_service_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет HTTP запрос к profile-service
        """
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers={"x-internal-request": "true"}
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Profile service error: {response.status_code} - {response.text}")
                    return None

        except httpx.ConnectError:
            logger.error(f"Cannot connect to profile-service at {self.base_url}")
            raise SearchServiceException("Profile service unavailable", status_code=503)
        except Exception as e:
            logger.error(f"Error making request to profile-service: {e}")
            raise SearchServiceException("Profile service error", status_code=500)

    async def get_profile_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение полного профиля по Keycloak ID
        GET /api/v1/internal/profiles/{keycloak_id}
        """
        return await self._make_request("GET", f"/api/v1/internal/profiles/{keycloak_id}")

    async def get_basic_profile(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение базового профиля (легковесный)
        GET /api/v1/internal/profiles/{keycloak_id}/basic
        """
        return await self._make_request("GET", f"/api/v1/internal/profiles/{keycloak_id}/basic")

    async def get_profiles_batch(self, keycloak_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получение нескольких профилей по Keycloak ID
        POST /api/v1/internal/profiles/batch
        """
        if not keycloak_ids:
            return []

        result = await self._make_request(
            "POST",
            "/api/v1/internal/profiles/batch",
            json_data={"keycloak_ids": keycloak_ids}
        )
        return result.get("profiles", []) if result else []

    async def get_profiles_count(self) -> int:
        """
        Получение общего количества профилей
        GET /api/v1/internal/profiles/count
        """
        result = await self._make_request("GET", "/api/v1/internal/profiles/count")
        return result.get("total", 0) if result else 0

    async def check_profiles_exist(self, keycloak_ids: List[str]) -> Dict[str, bool]:
        """
        Проверка существования профилей по Keycloak ID
        POST /api/v1/internal/profiles/exist
        """
        if not keycloak_ids:
            return {}

        result = await self._make_request(
            "POST",
            "/api/v1/internal/profiles/exist",
            json_data={"keycloak_ids": keycloak_ids}
        )
        return result.get("exist_map", {}) if result else {pid: False for pid in keycloak_ids}

    async def search_profiles(self, search_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Поиск профилей с фильтрацией
        
        Параметры:
            - gender: пол
            - min_age: минимальный возраст
            - max_age: максимальный возраст
            - city: город
            - education: образование
            - hobbies_keywords: ключевые слова интересов
            - partner_preferences: предпочтения партнера
            - online_only: только онлайн
            - exclude_keycloak_id: ID пользователя для исключения
            - exclude_keycloak_ids: список ID для исключения (НОВОЕ)
            - page: номер страницы
            - limit: размер страницы
        """
        return await self._make_request(
            "POST",
            "/api/v1/internal/profiles/search",
            json_data=search_params
        )


# Глобальный экземпляр клиента
_profile_client = None


def get_profile_client() -> ProfileServiceClient:
    global _profile_client
    if _profile_client is None:
        _profile_client = ProfileServiceClient()
    return _profile_client