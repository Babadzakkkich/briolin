import httpx
from typing import Optional, Dict, Any
from app.core.logger import logger


class MatchingServiceClient:
    """Клиент для получения данных о матчах из matching-service"""
    
    def __init__(self):
        self.base_url = "http://matching-service:8006"
        self.timeout = httpx.Timeout(5.0)
    
    async def _request(self, method: str, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Универсальный метод для запросов к matching-service"""
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method, url, params=params,
                    headers={"x-internal-request": "true"}
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"Matching service error {response.status_code}: {response.text}")
                    return None
        except httpx.ConnectError:
            logger.error(f"Cannot connect to matching-service at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Matching service request error: {e}")
            return None
    
    async def get_match_answers(
        self, 
        match_id: int, 
        keycloak_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получение ответов на вопросы для матча.
        GET /api/v1/matching/internal/matches/{match_id}/answers?user_id=...
        """
        return await self._request(
            "GET",
            f"/api/v1/internal/matches/{match_id}/answers",
            params={"user_id": keycloak_id}
        )


_matching_client = None

def get_matching_client() -> MatchingServiceClient:
    global _matching_client
    if _matching_client is None:
        _matching_client = MatchingServiceClient()
    return _matching_client