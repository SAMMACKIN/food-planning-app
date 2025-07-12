"""
RecipeV2 Pydantic schemas - simple and clean
"""
from typing import List, Optional
from pydantic import BaseModel


class RecipeV2Create(BaseModel):
    """Schema for creating a new recipe"""
    name: str
    description: Optional[str] = ""
    prep_time: int  # minutes
    difficulty: str  # Easy, Medium, Hard
    servings: int
    ingredients: List[str]
    instructions: List[str]
    tags: List[str] = []
    nutrition_notes: Optional[str] = ""
    source: Optional[str] = "manual"
    ai_generated: Optional[str] = "false"


class RecipeV2Update(BaseModel):
    """Schema for updating a recipe"""
    name: Optional[str] = None
    description: Optional[str] = None
    prep_time: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    nutrition_notes: Optional[str] = None


class RecipeV2Response(BaseModel):
    """Schema for recipe responses"""
    id: str
    user_id: str
    name: str
    description: str
    prep_time: int
    difficulty: str
    servings: int
    ingredients: List[str]
    instructions: List[str]
    tags: List[str]
    nutrition_notes: str
    source: str
    ai_generated: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}