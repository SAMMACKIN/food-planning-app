"""
Pantry and ingredient-related Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel


class IngredientResponse(BaseModel):
    id: str
    name: str
    category: str
    unit: str
    calories_per_unit: float = 0
    protein_per_unit: float = 0
    carbs_per_unit: float = 0
    fat_per_unit: float = 0
    allergens: list = []
    created_at: str


class PantryItemCreate(BaseModel):
    ingredient_id: str
    quantity: float
    expiration_date: Optional[str] = None


class PantryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    expiration_date: Optional[str] = None


class PantryItemResponse(BaseModel):
    user_id: str
    ingredient_id: str
    ingredient: IngredientResponse
    quantity: float
    expiration_date: Optional[str] = None
    updated_at: str
