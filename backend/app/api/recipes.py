"""
RecipeV2 API - Ultra simple, no complexity
"""
import logging
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.database import get_db
from ..core.auth_service import AuthService
from ..models.recipe_v2 import RecipeV2
from ..schemas.recipe_v2 import RecipeV2Create, RecipeV2Update, RecipeV2Response, IngredientNeeded

router = APIRouter(tags=["recipes"])
logger = logging.getLogger(__name__)


def get_current_user_simple(authorization: str = Header(None)):
    """Simple auth helper"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        token = authorization.split(" ")[1]
        user = AuthService.verify_user_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("", response_model=RecipeV2Response)
def save_recipe(
    recipe_data: RecipeV2Create,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Save a new recipe - dead simple"""
    try:
        # Convert user ID to UUID
        user_uuid = uuid.UUID(current_user["id"])
        
        # Convert ingredients_needed to JSON-serializable format
        ingredients_data = []
        for ingredient in recipe_data.ingredients_needed:
            if hasattr(ingredient, 'dict'):
                # It's a Pydantic model
                ingredients_data.append(ingredient.dict())
            else:
                # It's already a dict (from our validator)
                ingredients_data.append(ingredient)
        
        # Create recipe
        recipe = RecipeV2(
            user_id=user_uuid,
            name=recipe_data.name,
            description=recipe_data.description,
            prep_time=recipe_data.prep_time,
            difficulty=recipe_data.difficulty,
            servings=recipe_data.servings,
            ingredients_needed=ingredients_data,
            instructions=recipe_data.instructions,
            tags=recipe_data.tags,
            nutrition_notes=recipe_data.nutrition_notes,
            pantry_usage_score=recipe_data.pantry_usage_score,
            source=recipe_data.source,
            ai_generated=recipe_data.ai_generated,
            ai_provider=recipe_data.ai_provider
        )
        
        # Save to database
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        logger.info(f"✅ Recipe saved: {recipe.id} by user {user_uuid}")
        
        # Convert ingredients back to IngredientNeeded objects
        ingredients_needed = [IngredientNeeded(**ingredient) for ingredient in recipe.ingredients_needed]
        
        # Return response
        return RecipeV2Response(
            id=str(recipe.id),
            user_id=str(recipe.user_id),
            name=recipe.name,
            description=recipe.description,
            prep_time=recipe.prep_time,
            difficulty=recipe.difficulty,
            servings=recipe.servings,
            ingredients_needed=ingredients_needed,
            instructions=recipe.instructions,
            tags=recipe.tags,
            nutrition_notes=recipe.nutrition_notes,
            pantry_usage_score=recipe.pantry_usage_score,
            source=recipe.source,
            ai_generated=recipe.ai_generated,
            ai_provider=recipe.ai_provider,
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Save recipe error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@router.get("", response_model=List[RecipeV2Response])
def list_recipes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get all recipes for current user"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        # Get recipes for user
        recipes = db.query(RecipeV2).filter(
            RecipeV2.user_id == user_uuid
        ).order_by(desc(RecipeV2.created_at)).all()
        
        # Convert to response format
        response_recipes = []
        for recipe in recipes:
            ingredients_needed = [IngredientNeeded(**ingredient) for ingredient in recipe.ingredients_needed]
            response_recipes.append(RecipeV2Response(
                id=str(recipe.id),
                user_id=str(recipe.user_id),
                name=recipe.name,
                description=recipe.description,
                prep_time=recipe.prep_time,
                difficulty=recipe.difficulty,
                servings=recipe.servings,
                ingredients_needed=ingredients_needed,
                instructions=recipe.instructions,
                tags=recipe.tags,
                nutrition_notes=recipe.nutrition_notes,
                pantry_usage_score=recipe.pantry_usage_score,
                source=recipe.source,
                ai_generated=recipe.ai_generated,
                ai_provider=recipe.ai_provider,
                created_at=recipe.created_at.isoformat(),
                updated_at=recipe.updated_at.isoformat()
            ))
        
        logger.info(f"📋 Listed {len(response_recipes)} recipes for user {user_uuid}")
        return response_recipes
        
    except Exception as e:
        logger.error(f"❌ List recipes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list recipes: {str(e)}")


@router.get("/{recipe_id}", response_model=RecipeV2Response)
def get_recipe(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get a single recipe by ID"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        
        # Get recipe
        recipe = db.query(RecipeV2).filter(
            RecipeV2.id == recipe_uuid,
            RecipeV2.user_id == user_uuid
        ).first()
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        ingredients_needed = [IngredientNeeded(**ingredient) for ingredient in recipe.ingredients_needed]
        
        return RecipeV2Response(
            id=str(recipe.id),
            user_id=str(recipe.user_id),
            name=recipe.name,
            description=recipe.description,
            prep_time=recipe.prep_time,
            difficulty=recipe.difficulty,
            servings=recipe.servings,
            ingredients_needed=ingredients_needed,
            instructions=recipe.instructions,
            tags=recipe.tags,
            nutrition_notes=recipe.nutrition_notes,
            pantry_usage_score=recipe.pantry_usage_score,
            source=recipe.source,
            ai_generated=recipe.ai_generated,
            ai_provider=recipe.ai_provider,
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get recipe error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}")


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Delete a recipe"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        
        # Get recipe
        recipe = db.query(RecipeV2).filter(
            RecipeV2.id == recipe_uuid,
            RecipeV2.user_id == user_uuid
        ).first()
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Delete recipe
        db.delete(recipe)
        db.commit()
        
        logger.info(f"🗑️ Recipe deleted: {recipe_uuid} by user {user_uuid}")
        return {"message": "Recipe deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete recipe error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")


@router.put("/{recipe_id}", response_model=RecipeV2Response)
def update_recipe(
    recipe_id: str,
    recipe_data: RecipeV2Update,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update a recipe"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        
        # Get recipe
        recipe = db.query(RecipeV2).filter(
            RecipeV2.id == recipe_uuid,
            RecipeV2.user_id == user_uuid
        ).first()
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Update fields with special handling for ingredients_needed
        update_data = recipe_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "ingredients_needed" and value is not None:
                # Convert IngredientNeeded objects to dict format
                converted_value = []
                for ingredient in value:
                    if hasattr(ingredient, 'dict'):
                        # It's a Pydantic model
                        converted_value.append(ingredient.dict())
                    else:
                        # It's already a dict (from our validator)
                        converted_value.append(ingredient)
                value = converted_value
            setattr(recipe, field, value)
        
        db.commit()
        db.refresh(recipe)
        
        logger.info(f"✏️ Recipe updated: {recipe_uuid} by user {user_uuid}")
        
        ingredients_needed = [IngredientNeeded(**ingredient) for ingredient in recipe.ingredients_needed]
        
        return RecipeV2Response(
            id=str(recipe.id),
            user_id=str(recipe.user_id),
            name=recipe.name,
            description=recipe.description,
            prep_time=recipe.prep_time,
            difficulty=recipe.difficulty,
            servings=recipe.servings,
            ingredients_needed=ingredients_needed,
            instructions=recipe.instructions,
            tags=recipe.tags,
            nutrition_notes=recipe.nutrition_notes,
            pantry_usage_score=recipe.pantry_usage_score,
            source=recipe.source,
            ai_generated=recipe.ai_generated,
            ai_provider=recipe.ai_provider,
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update recipe error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")


@router.get("/debug/health")
def recipes_health_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Health check endpoint for recipes system"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        # Check database connection and table
        recipe_count = db.query(RecipeV2).filter(RecipeV2.user_id == user_uuid).count()
        
        return {
            "status": "healthy",
            "service": "recipes_v2",
            "user_id": str(user_uuid),
            "user_recipe_count": recipe_count,
            "database_connected": True,
            "table_accessible": True
        }
        
    except Exception as e:
        logger.error(f"❌ Recipes health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "recipes_v2", 
            "error": str(e),
            "database_connected": False,
            "table_accessible": False
        }