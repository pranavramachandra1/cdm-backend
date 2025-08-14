from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    user_id: str
    list_id: str
    task_name: str
    reminders: List[datetime]
    isPriority: bool
    isRecurring: bool
    list_version: int
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    user_id: Optional[str] = None
    list_id: Optional[str] = None
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    reminders: Optional[List[datetime]] = None
    isComplete: Optional[bool] = None
    isPriority: Optional[bool] = None
    isRecurring: Optional[bool] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    list_version: Optional[int] = None
    description: Optional[str] = None


class TaskResponse(BaseModel):
    user_id: str
    list_id: str
    task_id: str
    task_name: str
    reminders: List[datetime]
    isComplete: bool
    isPriority: bool
    isRecurring: bool
    createdAt: datetime
    updatedAt: datetime
    list_version: int
    description: Optional[str] = None