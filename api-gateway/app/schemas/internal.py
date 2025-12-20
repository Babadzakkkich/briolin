from pydantic import BaseModel, Field
from typing import Optional, List

class InternalUserCheck(BaseModel):
    exists: bool
    is_active: Optional[bool] = None