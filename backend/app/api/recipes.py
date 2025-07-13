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
from ..models.recipe_rating import RecipeRating
from ..schemas.recipe_v2 import RecipeV2Create, RecipeV2Update, RecipeV2Response, IngredientNeeded
from ..schemas.recipe_rating import RecipeRatingCreate, RecipeRatingUpdate, RecipeRatingResponse

router = APIRouter(tags=["recipes"])
logger = logging.getLogger(__name__)


def calculate_average_rating(db: Session, recipe_id: uuid.UUID) -> float:
    """Calculate average rating for a recipe"""
    ratings = db.query(RecipeRating).filter(RecipeRating.recipe_id == recipe_id).all()
    if not ratings:
        return None
    total = sum(r.rating for r in ratings)
    return round(total / len(ratings), 1)


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
        logger.info(f"💾 Attempting to save recipe: {recipe_data.name}")
        logger.info(f"💾 Recipe data: {recipe_data.dict()}")
        
        # Convert user ID to UUID
        user_uuid = uuid.UUID(current_user["id"])
        logger.info(f"💾 User UUID: {user_uuid}")
        
        # Convert ingredients_needed to JSON-serializable format
        ingredients_data = []
        logger.info(f"💾 Processing {len(recipe_data.ingredients_needed)} ingredients")
        for ingredient in recipe_data.ingredients_needed:
            if hasattr(ingredient, 'dict'):
                # It's a Pydantic model
                ingredients_data.append(ingredient.dict())
            else:
                # It's already a dict (from our validator)
                ingredients_data.append(ingredient)
        
        # Create recipe
        logger.info(f"💾 Creating RecipeV2 object...")
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
        logger.info(f"💾 Saving to database...")
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        logger.info(f"💾 Database save complete. Recipe ID: {recipe.id}")
        
        logger.info(f"✅ Recipe saved: {recipe.id} by user {user_uuid}")
        
        # Convert ingredients back to IngredientNeeded objects
        logger.info(f"💾 Converting ingredients for response...")
        ingredients_needed = [IngredientNeeded(**ingredient) for ingredient in recipe.ingredients_needed]
        
        # Return response
        logger.info(f"💾 Creating response object...")
        response = RecipeV2Response(
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
            rating=None,  # Temporarily disable rating calculation
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat()
        )
        logger.info(f"💾 Response created successfully")
        return response
        
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
        logger.info(f"📋 Fetching recipes for user: {user_uuid}")
        
        # Get recipes for user
        recipes = db.query(RecipeV2).filter(
            RecipeV2.user_id == user_uuid
        ).order_by(desc(RecipeV2.created_at)).all()
        
        logger.info(f"📋 Found {len(recipes)} recipes in database for user {user_uuid}")
        if recipes:
            logger.info(f"📋 Sample recipe IDs: {[str(r.id) for r in recipes[:3]]}")
        
        # Convert to response format (simplified like production)
        response_recipes = []
        for recipe in recipes:
            try:
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
                    rating=None,  # Temporarily disable rating calculation
                    created_at=recipe.created_at.isoformat(),
                    updated_at=recipe.updated_at.isoformat()
                ))
                logger.info(f"✅ Successfully processed recipe {recipe.id}: {recipe.name}")
            except Exception as recipe_error:
                logger.error(f"❌ Error processing recipe {recipe.id}: {recipe_error}")
                # Skip malformed recipes rather than failing the whole request
                continue
        
        logger.info(f"📋 Successfully processed {len(response_recipes)} out of {len(recipes)} recipes for user {user_uuid}")
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
            rating=calculate_average_rating(db, recipe.id),
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
            rating=calculate_average_rating(db, recipe.id),
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


# Recipe Rating endpoints
@router.post("/{recipe_id}/ratings", response_model=RecipeRatingResponse)
def rate_recipe(
    recipe_id: str,
    rating_data: RecipeRatingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Rate a recipe"""
    try:
        logger.info(f"⭐ Attempting to rate recipe {recipe_id}")
        logger.info(f"⭐ Rating data: {rating_data.dict()}")
        
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        logger.info(f"⭐ User UUID: {user_uuid}, Recipe UUID: {recipe_uuid}")
        
        # Verify recipe exists and belongs to user or is accessible
        recipe = db.query(RecipeV2).filter(RecipeV2.id == recipe_uuid).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if user already rated this recipe
        existing_rating = db.query(RecipeRating).filter(
            RecipeRating.recipe_id == recipe_uuid,
            RecipeRating.user_id == user_uuid
        ).first()
        
        if existing_rating:
            raise HTTPException(status_code=400, detail="You have already rated this recipe")
        
        # Create new rating
        new_rating = RecipeRating(
            recipe_id=recipe_uuid,
            user_id=user_uuid,
            rating=rating_data.rating,
            review_text=rating_data.review_text,
            would_make_again=rating_data.would_make_again,
            cooking_notes=rating_data.cooking_notes
        )
        
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        
        logger.info(f"⭐ Recipe rated: {recipe_uuid} by user {user_uuid} - {rating_data.rating}/5")
        
        return RecipeRatingResponse(
            id=str(new_rating.id),
            recipe_id=str(new_rating.recipe_id),
            user_id=str(new_rating.user_id),
            rating=new_rating.rating,
            review_text=new_rating.review_text,
            would_make_again=new_rating.would_make_again,
            cooking_notes=new_rating.cooking_notes,
            created_at=new_rating.created_at.isoformat(),
            updated_at=new_rating.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Rate recipe error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rate recipe: {str(e)}")


@router.get("/{recipe_id}/ratings", response_model=List[RecipeRatingResponse])
def get_recipe_ratings(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get all ratings for a recipe"""
    try:
        recipe_uuid = uuid.UUID(recipe_id)
        
        # Verify recipe exists
        recipe = db.query(RecipeV2).filter(RecipeV2.id == recipe_uuid).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Get ratings for this recipe
        ratings = db.query(RecipeRating).filter(
            RecipeRating.recipe_id == recipe_uuid
        ).order_by(desc(RecipeRating.created_at)).all()
        
        return [
            RecipeRatingResponse(
                id=str(rating.id),
                recipe_id=str(rating.recipe_id),
                user_id=str(rating.user_id),
                rating=rating.rating,
                review_text=rating.review_text,
                would_make_again=rating.would_make_again,
                cooking_notes=rating.cooking_notes,
                created_at=rating.created_at.isoformat(),
                updated_at=rating.updated_at.isoformat()
            )
            for rating in ratings
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get recipe ratings error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe ratings: {str(e)}")


@router.put("/{recipe_id}/ratings/{rating_id}", response_model=RecipeRatingResponse)
def update_recipe_rating(
    recipe_id: str,
    rating_id: str,
    rating_data: RecipeRatingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update a recipe rating"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        rating_uuid = uuid.UUID(rating_id)
        
        # Get rating
        rating = db.query(RecipeRating).filter(
            RecipeRating.id == rating_uuid,
            RecipeRating.recipe_id == recipe_uuid,
            RecipeRating.user_id == user_uuid
        ).first()
        
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found or access denied")
        
        # Update fields
        update_data = rating_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rating, field, value)
        
        db.commit()
        db.refresh(rating)
        
        logger.info(f"✏️ Recipe rating updated: {rating_uuid} by user {user_uuid}")
        
        return RecipeRatingResponse(
            id=str(rating.id),
            recipe_id=str(rating.recipe_id),
            user_id=str(rating.user_id),
            rating=rating.rating,
            review_text=rating.review_text,
            would_make_again=rating.would_make_again,
            cooking_notes=rating.cooking_notes,
            created_at=rating.created_at.isoformat(),
            updated_at=rating.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update recipe rating error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update recipe rating: {str(e)}")


@router.delete("/{recipe_id}/ratings/{rating_id}")
def delete_recipe_rating(
    recipe_id: str,
    rating_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Delete a recipe rating"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        recipe_uuid = uuid.UUID(recipe_id)
        rating_uuid = uuid.UUID(rating_id)
        
        # Get rating
        rating = db.query(RecipeRating).filter(
            RecipeRating.id == rating_uuid,
            RecipeRating.recipe_id == recipe_uuid,
            RecipeRating.user_id == user_uuid
        ).first()
        
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found or access denied")
        
        # Delete rating
        db.delete(rating)
        db.commit()
        
        logger.info(f"🗑️ Recipe rating deleted: {rating_uuid} by user {user_uuid}")
        return {"message": "Rating deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete recipe rating error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe rating: {str(e)}")