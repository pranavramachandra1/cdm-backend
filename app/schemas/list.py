from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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


class ListResponse(BaseModel):
    list_id: str
    user_id: str
    list_name: str
    created_at: datetime
    last_updated_at: datetime
    version: int
