"""
Ingredients API endpoints
"""
import json
from typing import List
from fastapi import APIRouter, HTTPException, Query

from ..core.database_service import get_db_session, db_service
from ..schemas.pantry import IngredientResponse
from ..models.ingredient import Ingredient

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=List[IngredientResponse])
async def get_ingredients():
    """Get all available ingredients"""
    with get_db_session() as session:
        ingredients = session.query(Ingredient).all()
        
        result = []
        for ingredient in ingredients:
            result.append(IngredientResponse(
                id=str(ingredient.id),
                name=ingredient.name,
                category=ingredient.category.name if ingredient.category else "Other",
                unit=ingredient.unit,
                calories_per_unit=ingredient.nutritional_info.get("calories", 0) if ingredient.nutritional_info else 0,
                protein_per_unit=ingredient.nutritional_info.get("protein", 0) if ingredient.nutritional_info else 0,
                carbs_per_unit=ingredient.nutritional_info.get("carbs", 0) if ingredient.nutritional_info else 0,
                fat_per_unit=ingredient.nutritional_info.get("fat", 0) if ingredient.nutritional_info else 0,
                allergens=ingredient.allergens or [],
                created_at=None  # Not available in new model
            ))
        
        return result


@router.get("/search", response_model=List[IngredientResponse])
async def search_ingredients(q: str = Query(..., description="Search query for ingredient name")):
    """Search ingredients by name"""
    with get_db_session() as session:
        ingredients = session.query(Ingredient).filter(
            Ingredient.name.ilike(f'%{q}%')
        ).limit(20).all()
        
        result = []
        for ingredient in ingredients:
            result.append(IngredientResponse(
                id=str(ingredient.id),
                name=ingredient.name,
                category=ingredient.category.name if ingredient.category else "Other",
                unit=ingredient.unit,
                calories_per_unit=ingredient.nutritional_info.get("calories", 0) if ingredient.nutritional_info else 0,
                protein_per_unit=ingredient.nutritional_info.get("protein", 0) if ingredient.nutritional_info else 0,
                carbs_per_unit=ingredient.nutritional_info.get("carbs", 0) if ingredient.nutritional_info else 0,
                fat_per_unit=ingredient.nutritional_info.get("fat", 0) if ingredient.nutritional_info else 0,
                allergens=ingredient.allergens or [],
                created_at=None  # Not available in new model
            ))
        
        return result