"""
Recipe rating schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class RecipeRatingCreate(BaseModel):
    recipe_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = True
    cooking_notes: Optional[str] = None


class RecipeRatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = None
    cooking_notes: Optional[str] = None


class RecipeRatingResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    rating: int
    review_text: Optional[str] = None
    would_make_again: bool = True
    cooking_notes: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True