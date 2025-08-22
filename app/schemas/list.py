from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# VALUES:
TOKEN_LENGTH = 43

# ENUMS:
class ListVisibilityLevel(Enum):
    PRIVATE = "PRIVATE"
    ORGANIZATION_ONLY = "ORGANIZATION_ONLY" 
    PUBLIC = "PUBLIC"

# Response Formats:

class ListCreate(BaseModel):
    user_id: str
    list_name: str

class ListUpdate(BaseModel):
    list_id: Optional[str] = None
    user_id: Optional[str] = None
    list_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    version: Optional[int] = None
    visibility: Optional[str] = None
    share_token: Optional[str] = None

class ListResponse(BaseModel):
    list_id: str
    user_id: str
    list_name: str
    created_at: datetime
    last_updated_at: datetime
    version: int
    visibility: Optional[str]
    share_token: Optional[str]
