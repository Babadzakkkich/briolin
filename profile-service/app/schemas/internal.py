from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from shared.schemas.shared import Gender

class KeycloakProfileUpdate(BaseModel):
    """Для обновления имени в Keycloak через auth-service"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

class ProfileDeleteData(BaseModel):
    """Данные для удаления профиля"""
    keycloak_id: str