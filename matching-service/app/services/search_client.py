import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import SearchServiceException


class SearchServiceClient:
    def __init__(self):
        self.base_url = settings.services.search_service_url
        self.timeout = httpx.Timeout(10.0)

    async def classic_search(
        self,
        keycloak_id: str,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        city: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Call search-service classic search endpoint"""
        url = f"{self.base_url}/api/v1/search/classic"
        payload = {
            "gender": gender,
            "min_age": min_age,
            "max_age": max_age,
            "city": city,
            "exclude_user_ids": exclude_ids or [],
            "page": (offset // limit) + 1,
            "limit": limit
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers={"x-internal-request": "true"})
                if response.status_code == 200:
                    data = response.json()
                    # Expected format: { "profiles": [...] }
                    return data.get("profiles", [])
                else:
                    logger.error(f"Search service error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Search service request failed: {e}")
            raise SearchServiceException("Search service unavailable")


search_client = SearchServiceClient()