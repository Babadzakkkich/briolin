from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from shared.schemas.shared import Gender


class KeycloakProfileUpdate(BaseModel):
    """Для обновления имени в Keycloak через auth-service"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description='Имя пользователя')
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description='Фамилия пользователя')


class ProfileDeleteData(BaseModel):
    """Данные для удаления профиля"""
    keycloak_id: str = Field(..., description='Уникальный идентификатор пользователя в Keycloak')


class BatchProfilesRequest(BaseModel):
    """Запрос на получение нескольких профилей"""
    profile_ids: List[int] = Field(..., min_items=1, max_items=100, description='Список внутренних идентификаторов профилей')


class SearchProfilesRequest(BaseModel):
    """Запрос на поиск профилей (для search-service)"""
    gender: Optional[str] = Field(None, description='Пол пользователя')
    min_age: Optional[int] = Field(None, ge=18, le=100, description='Минимальный возраст пользователя для поиска')
    max_age: Optional[int] = Field(None, ge=18, le=100, description='Максимальный возраст пользователя для поиска')
    city: Optional[str] = Field(None, description='Город пользователя')
    education: Optional[str] = Field(None, description='Информация об образовании пользователя')
    hobbies_keywords: Optional[List[str]] = Field(None, description='Ключевые слова для фильтрации по увлечениям')
    partner_preferences: Optional[str] = Field(None, description='Описание предпочтений пользователя к потенциальному партнёру')
    online_only: bool = Field(False, description='Признак поиска только среди пользователей, находящихся онлайн')
    exclude_user_id: Optional[int] = Field(None, description='Внутренний идентификатор пользователя, исключаемого из результатов поиска')
    exclude_keycloak_id: Optional[str] = Field(None, description='Keycloak ID пользователя, исключаемого из результатов поиска')
    page: int = Field(1, ge=1, description='Номер страницы результатов')
    limit: int = Field(10, ge=1, le=100, description='Максимальное количество элементов в результате')

class SearchByEmbeddingRequest(BaseModel):
    """Внутренняя схема запроса на поиск профилей по векторному представлению."""
    embedding: List[float] = Field(..., description='Векторное представление профиля для поиска по сходству')
    filters: Dict[str, Any] = Field(default_factory=dict, description='Дополнительные фильтры поиска')
    exclude_ids: List[str] = Field(default_factory=list, description='Идентификаторы пользователей, исключаемых из результатов поиска')
    limit: int = Field(50, ge=1, le=100, description='Максимальное количество элементов в результате')
    offset: int = Field(0, ge=0, description='Смещение относительно начала набора результатов')


class SearchByEmbeddingResponse(BaseModel):
    """Внутренняя схема ответа с профилями, найденными по векторному представлению."""
    profiles: List[Dict[str, Any]] = Field(..., description='Список профилей пользователей')