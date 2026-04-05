from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from shared.schemas.shared import Gender


class ClassicRecommendationFilters(BaseModel):
    gender: Optional[Gender] = None
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    city: Optional[str] = None


class TargetedRecommendationFilters(ClassicRecommendationFilters):
    education: Optional[str] = None
    hobbies_keywords: Optional[List[str]] = None
    online_only: bool = False


class RecommendationProfile(BaseModel):
    keycloak_id: str
    display_name: str
    age: int
    city: str
    avatar_url: Optional[str] = None
    similarity: Optional[float] = None