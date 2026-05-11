from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PartnerInfo(BaseModel):
    keycloak_id: str
    display_name: str
    avatar_url: Optional[str] = None


class MatchResponse(BaseModel):
    match_id: int
    partner: PartnerInfo
    matched_at: datetime