"""
Family member-related Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel


class FamilyMemberCreate(BaseModel):
    name: str
    age: Optional[int] = None
    dietary_restrictions: Optional[list] = []
    preferences: Optional[dict] = {}


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    dietary_restrictions: Optional[list] = None
    preferences: Optional[dict] = None


class FamilyMemberResponse(BaseModel):
    id: str
    user_id: str
    name: str
    age: Optional[int] = None
    dietary_restrictions: list = []
    preferences: dict = {}
    created_at: str
