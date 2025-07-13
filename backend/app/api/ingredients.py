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
    try:
        with get_db_session() as session:
            from sqlalchemy.orm import joinedload
            ingredients = session.query(Ingredient).options(joinedload(Ingredient.category)).all()
            
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching ingredients: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching ingredients: {str(e)}")


@router.get("/search", response_model=List[IngredientResponse])
async def search_ingredients(q: str = Query(..., description="Search query for ingredient name or category")):
    """Search ingredients by name or category"""
    try:
        with get_db_session() as session:
            from sqlalchemy.orm import joinedload
            from sqlalchemy import or_
            from ..models.ingredient import IngredientCategory
            
            # Enhanced search: ingredient name OR category name
            # Also handle common search terms like "meat", "protein", etc.
            search_term = q.lower().strip()
            
            # Map common search terms to multiple categories
            category_mappings = {
                "meat": ["Meat & Poultry"],
                "protein": ["Meat & Poultry", "Fish & Seafood", "Legumes & Plant Proteins", "Eggs & Dairy Proteins"],
                "proteins": ["Meat & Poultry", "Fish & Seafood", "Legumes & Plant Proteins", "Eggs & Dairy Proteins"],
                "fish": ["Fish & Seafood"],
                "seafood": ["Fish & Seafood"],
                "dairy": ["Dairy", "Eggs & Dairy Proteins"],
                "vegetables": ["Vegetables"],
                "fruits": ["Fruits"],
                "grains": ["Grains & Starches"],
                "nuts": ["Nuts & Seeds"],
                "seeds": ["Nuts & Seeds"],
                "spices": ["Herbs & Spices"],
                "herbs": ["Herbs & Spices"],
                "oils": ["Oils & Condiments"],
                "condiments": ["Oils & Condiments"]
            }
            
            # Start with name-based search
            query_conditions = [Ingredient.name.ilike(f'%{q}%')]
            
            # Add category-based search conditions
            if search_term in category_mappings:
                # Search across multiple related categories
                category_names = category_mappings[search_term]
                for cat_name in category_names:
                    query_conditions.append(
                        Ingredient.category.has(IngredientCategory.name.ilike(f'%{cat_name}%'))
                    )
            else:
                # Direct category name search
                query_conditions.append(
                    Ingredient.category.has(IngredientCategory.name.ilike(f'%{q}%'))
                )
            
            ingredients = session.query(Ingredient).options(joinedload(Ingredient.category)).filter(
                or_(*query_conditions)
            ).limit(50).all()  # Increased limit for category searches
            
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching ingredients: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching ingredients: {str(e)}")