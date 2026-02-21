from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from shared.schemas.shared import Gender


class KeycloakProfileUpdate(BaseModel):
    """Для обновления имени в Keycloak через auth-service"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)


class ProfileDeleteData(BaseModel):
    """Данные для удаления профиля"""
    keycloak_id: str


class BatchProfilesRequest(BaseModel):
    """Запрос на получение нескольких профилей"""
    profile_ids: List[int] = Field(..., min_items=1, max_items=100)


class SearchProfilesRequest(BaseModel):
    """Запрос на поиск профилей (для search-service)"""
    gender: Optional[str] = None
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    city: Optional[str] = None
    education: Optional[str] = None
    hobbies_keywords: Optional[List[str]] = None
    partner_preferences: Optional[str] = None
    online_only: bool = False
    exclude_user_id: Optional[int] = None
    exclude_keycloak_id: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)