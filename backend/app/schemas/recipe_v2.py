"""
RecipeV2 Pydantic schemas - compatible with frontend
"""
from typing import List, Optional
from pydantic import BaseModel


class IngredientNeeded(BaseModel):
    """Individual ingredient with details"""
    name: str
    quantity: str  # String as frontend sends it
    unit: str
    have_in_pantry: bool


class RecipeV2Create(BaseModel):
    """Schema for creating a new recipe - matches frontend exactly"""
    name: str
    description: str
    prep_time: int  # minutes
    difficulty: str  # Easy, Medium, Hard
    servings: int
    ingredients_needed: List[IngredientNeeded]  # Match frontend field name
    instructions: List[str]
    tags: List[str] = []
    nutrition_notes: str
    pantry_usage_score: int
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None
    source: Optional[str] = "user_created"


class RecipeV2Update(BaseModel):
    """Schema for updating a recipe"""
    name: Optional[str] = None
    description: Optional[str] = None
    prep_time: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    ingredients_needed: Optional[List[IngredientNeeded]] = None
    instructions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    nutrition_notes: Optional[str] = None
    pantry_usage_score: Optional[int] = None


class RecipeV2Response(BaseModel):
    """Schema for recipe responses"""
    id: str
    user_id: str
    name: str
    description: str
    prep_time: int
    difficulty: str
    servings: int
    ingredients_needed: List[IngredientNeeded]
    instructions: List[str]
    tags: List[str]
    nutrition_notes: str
    pantry_usage_score: int
    source: str
    ai_generated: bool
    ai_provider: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}