from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ProfileQuestionsCreate(BaseModel):
    question_1: str = Field(..., min_length=10, max_length=500)
    question_2: str = Field(..., min_length=10, max_length=500)
    question_3: str = Field(..., min_length=10, max_length=500)
    question_4: str = Field(..., min_length=10, max_length=500)
    question_5: str = Field(..., min_length=10, max_length=500)


class ProfileQuestionsUpdate(BaseModel):
    question_1: Optional[str] = Field(None, min_length=10, max_length=500)
    question_2: Optional[str] = Field(None, min_length=10, max_length=500)
    question_3: Optional[str] = Field(None, min_length=10, max_length=500)
    question_4: Optional[str] = Field(None, min_length=10, max_length=500)
    question_5: Optional[str] = Field(None, min_length=10, max_length=500)


class ProfileQuestionsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    question_1: str
    question_2: str
    question_3: str
    question_4: str
    question_5: str
    created_at: datetime
    updated_at: datetime