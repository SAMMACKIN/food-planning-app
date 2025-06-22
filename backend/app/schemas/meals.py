"""
Meal planning and recommendation-related Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel


class MealRecommendationRequest(BaseModel):
    num_recommendations: Optional[int] = 5
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    preferences: Optional[dict] = {}
    ai_provider: Optional[str] = "claude"  # claude or groq


class MealRecommendationResponse(BaseModel):
    name: str
    description: str
    prep_time: int
    difficulty: str
    servings: int
    ingredients_needed: list
    instructions: list
    tags: list
    nutrition_notes: str
    pantry_usage_score: int
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None


class MealPlanCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    meal_type: str  # breakfast, lunch, dinner, snack
    meal_name: str
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None


class MealPlanUpdate(BaseModel):
    meal_name: Optional[str] = None
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None


class MealPlanResponse(BaseModel):
    id: str
    user_id: str
    date: str
    meal_type: str
    meal_name: str
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None
    ai_generated: bool = False
    ai_provider: Optional[str] = None
    created_at: str


class MealReviewCreate(BaseModel):
    rating: int  # 1-5 stars
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = True
    preparation_notes: Optional[str] = None


class MealReviewUpdate(BaseModel):
    rating: Optional[int] = None
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = None
    preparation_notes: Optional[str] = None


class MealReviewResponse(BaseModel):
    id: str
    meal_plan_id: str
    user_id: str
    rating: int
    review_text: Optional[str] = None
    would_make_again: bool = True
    preparation_notes: Optional[str] = None
    reviewed_at: str
