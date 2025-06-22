"""
Authentication and user-related Pydantic schemas
"""
import re
from typing import Optional
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Allow 'admin' as a special case
        if v == 'admin':
            return v
        # Otherwise validate as email using simple regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, v):
            return v
        raise ValueError('Invalid email format')


class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Allow 'admin' as a special case
        if v == 'admin':
            return v
        # Otherwise validate as email using simple regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, v):
            return v
        raise ValueError('Invalid email format')


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool = True
    is_admin: bool = False
    created_at: str


class PasswordResetRequest(BaseModel):
    email: str