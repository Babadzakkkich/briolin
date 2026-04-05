import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import ProfileServiceException


class ProfileServiceClient:
    def __init__(self):
        self.base_url = settings.services.profile_service_url
        self.timeout = httpx.Timeout(10.0)

    async def _request(self, method: str, path: str, json: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method, url, json=json,
                    headers={"x-internal-request": "true"}
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Profile service error {response.status_code}: {response.text}")
                    return None
        except httpx.ConnectError:
            logger.error(f"Cannot connect to profile-service at {self.base_url}")
            raise ProfileServiceException("Profile service unavailable")
        except Exception as e:
            logger.error(f"Profile service request error: {e}")
            raise ProfileServiceException("Profile service error")

    async def get_basic_profile(self, keycloak_id: str) -> Optional[Dict]:
        """GET /api/v1/internal/profiles/{keycloak_id}/basic"""
        return await self._request("GET", f"/api/v1/internal/profiles/{keycloak_id}/basic")

    async def get_embedding(self, keycloak_id: str) -> Optional[List[float]]:
        """GET /api/v1/internal/profiles/{keycloak_id}/embedding"""
        result = await self._request("GET", f"/api/v1/internal/profiles/{keycloak_id}/embedding")
        if result:
            return result.get("embedding")
        return None

    async def search_by_embedding(
        self,
        embedding: List[float],
        filters: Dict[str, Any],
        exclude_ids: List[str],
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """POST /api/v1/internal/profiles/search_by_embedding"""
        payload = {
            "embedding": embedding,
            "filters": filters,
            "exclude_ids": exclude_ids,
            "limit": limit,
            "offset": offset
        }
        result = await self._request("POST", "/api/v1/internal/profiles/search_by_embedding", json=payload)
        if result:
            return result.get("profiles", [])
        return []


profile_client = ProfileServiceClient()