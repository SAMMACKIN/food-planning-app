"""
Pydantic schemas for content sharing
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from ..models.content import ContentType


class ContentShareCreate(BaseModel):
    """Schema for creating a content share"""
    content_type: ContentType
    content_id: str
    shared_with_email: EmailStr
    message: Optional[str] = None

    class Config:
        use_enum_values = True


class ContentShareResponse(BaseModel):
    """Schema for content share response"""
    id: str
    content_type: ContentType
    content_id: str
    shared_by_user_email: str
    shared_with_user_email: str
    share_message: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        use_enum_values = True


class SharedContentResponse(BaseModel):
    """Schema for content shared with a user"""
    share_id: str
    content_type: ContentType
    content_id: str
    content_title: str
    content_description: str
    shared_by_user_name: str
    shared_by_user_email: str
    share_message: Optional[str]
    shared_at: datetime

    class Config:
        use_enum_values = True


class UserProfileResponse(BaseModel):
    """Schema for user profile information"""
    name: Optional[str]
    email: str
    books_count: int
    tv_shows_count: int
    movies_count: int
    recipes_count: int


class PublicUserProfile(BaseModel):
    """Schema for public user profile"""
    name: str
    email: str
    books_count: int
    tv_shows_count: int
    movies_count: int
    recipes_count: int
    member_since: datetime


class AddToListRequest(BaseModel):
    """Schema for adding shared content to personal list"""
    share_id: str