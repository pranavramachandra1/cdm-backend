from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone_number: str
    first_name: str
    last_name: str
    google_id: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v, info: ValidationInfo):
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    google_id: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    phone_number: str
    first_name: str
    last_name: str
    created_at: datetime
    last_updated_at: datetime
