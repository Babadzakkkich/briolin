from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from enum import Enum


class EmailType(str, Enum):
    WELCOME = "welcome"
    LOGIN = "login"
    TEST_COMPLETE = "test_complete"


class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailTemplate(BaseModel):
    to: EmailStr
    template: EmailType
    context: Dict[str, Any] = Field(default_factory=dict)


class BulkEmailRequest(BaseModel):
    recipients: list[EmailStr]
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailResponse(BaseModel):
    success: bool
    message: str
    to: EmailStr


class EmailNotification(BaseModel):
    type: EmailType
    to: EmailStr
    name: Optional[str] = None
    timestamp: Optional[str] = None
    test_name: Optional[str] = None
    score: Optional[int] = None
    total: Optional[int] = None
    percentage: Optional[float] = None