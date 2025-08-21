from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional

class UserTokenCreate(BaseModel):
    user_id: str
    provider: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    scope: str


class UserTokenUpdate(BaseModel):
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    scope: Optional[str]

class UserTokenResponse(BaseModel):
    pauser_id: str
    provider: str
    token_type: str
    expires_at: datetime
    scope: str
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator('is_expired')
    @classmethod
    def calculate_expiration(cls, v, info: ValidationInfo):
        expires_at = info.data.get('expires_at')
        if expires_at:
            return datetime.utcnow() > expires_at
        return True
    
class UserTokenInternal(BaseModel):
    """Internal model with sensitive data - for service layer only"""
    _id: Optional[str] = None
    user_id: str
    provider: str
    access_token: str  # This should be encrypted in storage
    refresh_token: str  # This should be encrypted in storage
    token_type: str
    expires_at: datetime
    scope: str
    created_at: datetime
    updated_at: datetime