"""
Saved recipes API endpoints - SQLAlchemy version
"""
import logging
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..schemas.meals import (
    SavedRecipeCreate, SavedRecipeUpdate, SavedRecipeResponse,
    RecipeRatingCreate, RecipeRatingUpdate, RecipeRatingResponse
)

router = APIRouter(tags=["recipes"])
logger = logging.getLogger(__name__)


def get_current_user(authorization: str = None):
    """Get current user using AuthService"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        user = AuthService.verify_user_token(token)
        if user:
            return {
                'sub': user['id'],
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'is_admin': user['is_admin']
            }
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


@router.get("", response_model=List[SavedRecipeResponse])
async def get_saved_recipes(
    search: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    authorization: str = Header(None)
):
    """Get user's saved recipes with optional filtering"""
    try:
        logger.info("🍽️ GET SAVED RECIPES ENDPOINT CALLED")
        logger.info(f"🔑 Authorization header present: {bool(authorization)}")
        
        current_user = get_current_user(authorization)
        if not current_user:
            logger.warning("🚫 No authentication provided")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user['sub']
        logger.info(f"👤 User authenticated: {current_user.get('email', 'unknown')} (ID: {user_id})")
        
        with get_db_session() as session:
            from ..models.recipe import SavedRecipe
            from sqlalchemy import and_
            import uuid as uuid_module
            
            # Convert user_id string to UUID object, same as AuthService
            try:
                user_uuid = uuid_module.UUID(user_id)
            except ValueError as e:
                logger.error(f"Invalid UUID format: {user_id} - {e}")
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            
            # Use SQLAlchemy ORM query like AuthService does - this handles UUID properly
            query = session.query(SavedRecipe).filter(SavedRecipe.user_id == user_uuid)
            
            # Add search filter
            if search:
                search_filter = f'%{search}%'
                query = query.filter(
                    and_(
                        SavedRecipe.name.ilike(search_filter) |
                        SavedRecipe.description.ilike(search_filter) |
                        SavedRecipe.tags.ilike(search_filter)
                    )
                )
            
            # Add difficulty filter  
            if difficulty:
                query = query.filter(SavedRecipe.difficulty == difficulty)
                
            # Add tags filter
            if tags:
                query = query.filter(SavedRecipe.tags.ilike(f'%{tags}%'))
            
            # Order by updated_at DESC
            query = query.order_by(SavedRecipe.updated_at.desc())
            
            # Execute query
            recipes_data = query.all()
            
            # Process ORM objects
            recipes = []
            for recipe in recipes_data:
                try:
                    # Parse JSON fields
                    try:
                        ingredients_needed = json.loads(recipe.ingredients_needed) if recipe.ingredients_needed else []
                    except (json.JSONDecodeError, TypeError):
                        ingredients_needed = []
                    
                    try:
                        instructions = json.loads(recipe.instructions) if recipe.instructions else []
                    except (json.JSONDecodeError, TypeError):
                        instructions = []
                    
                    try:
                        tags = json.loads(recipe.tags) if recipe.tags else []
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                    
                    # Create response using ORM object attributes
                    recipe_response = SavedRecipeResponse(
                        id=str(recipe.id),
                        user_id=str(recipe.user_id),
                        name=recipe.name,
                        description=recipe.description or "",
                        prep_time=recipe.prep_time,
                        difficulty=recipe.difficulty,
                        servings=recipe.servings,
                        ingredients_needed=ingredients_needed,
                        instructions=instructions,
                        tags=tags,
                        nutrition_notes=recipe.nutrition_notes or "",
                        pantry_usage_score=recipe.pantry_usage_score or 0,
                        ai_generated=recipe.ai_generated or False,
                        ai_provider=recipe.ai_provider,
                        source=recipe.source or "manual",
                        times_cooked=recipe.times_cooked or 0,
                        last_cooked=recipe.last_cooked.isoformat() if recipe.last_cooked else None,
                        rating=None,  # No rating data for now
                        created_at=recipe.created_at.isoformat() if recipe.created_at else None,
                        updated_at=recipe.updated_at.isoformat() if recipe.updated_at else None
                    )
                    recipes.append(recipe_response)
                    
                except Exception as e:
                    logger.error(f"Error processing recipe {recipe.name if hasattr(recipe, 'name') else 'unknown'}: {e}")
                    # Continue processing other recipes instead of failing completely
                    continue
            
            return recipes
        
    except Exception as e:
        logger.error(f"💥 Critical error in get_saved_recipes: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching saved recipes: {str(e)}")


@router.post("", response_model=SavedRecipeResponse)
async def save_recipe(recipe_data: SavedRecipeCreate, authorization: str = Header(None)):
    """Save a new recipe"""
    logger.info(f"🍽️ Recipe save request: {recipe_data.name}")
    
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    recipe_id = str(uuid.uuid4())
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        # Validate required fields
        if not recipe_data.name or not recipe_data.description:
            raise HTTPException(status_code=400, detail="Recipe name and description are required")
        
        if recipe_data.prep_time <= 0 or recipe_data.servings <= 0:
            raise HTTPException(status_code=400, detail="Prep time and servings must be positive numbers")
        
        # Insert new saved recipe using PostgreSQL syntax
        session.execute(text('''
            INSERT INTO saved_recipes 
            (id, user_id, name, description, prep_time, difficulty, servings, 
             ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
             ai_generated, ai_provider, source)
            VALUES (:id, :user_id, :name, :description, :prep_time, :difficulty, :servings, 
                    :ingredients_needed, :instructions, :tags, :nutrition_notes, :pantry_usage_score,
                    :ai_generated, :ai_provider, :source)
        '''), {
            'id': recipe_id, 'user_id': user_id, 'name': recipe_data.name, 'description': recipe_data.description,
            'prep_time': recipe_data.prep_time, 'difficulty': recipe_data.difficulty, 'servings': recipe_data.servings,
            'ingredients_needed': json.dumps(recipe_data.ingredients_needed), 
            'instructions': json.dumps(recipe_data.instructions),
            'tags': json.dumps(recipe_data.tags),
            'nutrition_notes': recipe_data.nutrition_notes, 'pantry_usage_score': recipe_data.pantry_usage_score,
            'ai_generated': recipe_data.ai_generated, 'ai_provider': recipe_data.ai_provider, 'source': recipe_data.source
        })
        
        # Get the created recipe
        result = session.execute(text('''
            SELECT id, user_id, name, description, prep_time, difficulty, servings, 
                   ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
                   ai_generated, ai_provider, source, times_cooked, last_cooked, created_at, updated_at
            FROM saved_recipes WHERE id = :recipe_id
        '''), {'recipe_id': recipe_id})
        recipe = result.fetchone()
        
        if not recipe:
            raise HTTPException(status_code=500, detail="Recipe was not saved properly")
        
        logger.info(f"✅ Recipe saved successfully: {recipe_id}")
        
        return SavedRecipeResponse(
            id=str(recipe[0]),  # Convert UUID to string
            user_id=str(recipe[1]),  # Convert UUID to string
            name=recipe[2],
            description=recipe[3],
            prep_time=recipe[4],
            difficulty=recipe[5],
            servings=recipe[6],
            ingredients_needed=json.loads(recipe[7]) if recipe[7] else [],
            instructions=json.loads(recipe[8]) if recipe[8] else [],
            tags=json.loads(recipe[9]) if recipe[9] else [],
            nutrition_notes=recipe[10],
            pantry_usage_score=recipe[11],
            ai_generated=bool(recipe[12]),
            ai_provider=recipe[13],
            source=recipe[14],
            times_cooked=recipe[15] or 0,
            last_cooked=recipe[16].isoformat() if recipe[16] else None,  # Convert datetime to string
            rating=None,
            created_at=recipe[17].isoformat() if recipe[17] else None,  # Convert datetime to string
            updated_at=recipe[18].isoformat() if recipe[18] else None   # Convert datetime to string
        )


@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_saved_recipe(recipe_id: str, authorization: str = Header(None)):
    """Get a specific saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        result = session.execute(text('''
            SELECT r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                   r.servings, r.ingredients_needed, r.instructions, r.tags, r.nutrition_notes,
                   r.pantry_usage_score, r.ai_generated, r.ai_provider, r.source,
                   r.times_cooked, r.last_cooked, r.created_at, r.updated_at,
                   AVG(rt.rating) as avg_rating
            FROM saved_recipes r
            LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
            WHERE r.id = :recipe_id AND r.user_id = :user_id
            GROUP BY r.id
        '''), {'recipe_id': recipe_id, 'user_id': user_id})
        
        recipe = result.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return SavedRecipeResponse(
            id=str(recipe[0]),  # Convert UUID to string
            user_id=str(recipe[1]),  # Convert UUID to string
            name=recipe[2],
            description=recipe[3],
            prep_time=recipe[4],
            difficulty=recipe[5],
            servings=recipe[6],
            ingredients_needed=json.loads(recipe[7]) if recipe[7] else [],
            instructions=json.loads(recipe[8]) if recipe[8] else [],
            tags=json.loads(recipe[9]) if recipe[9] else [],
            nutrition_notes=recipe[10],
            pantry_usage_score=recipe[11],
            ai_generated=bool(recipe[12]),
            ai_provider=recipe[13],
            source=recipe[14],
            times_cooked=recipe[15] or 0,
            last_cooked=recipe[16].isoformat() if recipe[16] else None,  # Convert datetime to string
            rating=float(recipe[19]) if recipe[19] else None,
            created_at=recipe[17].isoformat() if recipe[17] else None,  # Convert datetime to string
            updated_at=recipe[18].isoformat() if recipe[18] else None   # Convert datetime to string
        )


@router.post("/{recipe_id}/ratings", response_model=RecipeRatingResponse)
async def rate_recipe(
    recipe_id: str, 
    rating_data: RecipeRatingCreate, 
    authorization: str = Header(None)
):
    """Rate a saved recipe"""
    logger.info(f"⭐ Recipe rating request: {recipe_id} with {rating_data.rating} stars")
    
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if rating_data.rating < 1 or rating_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    user_id = current_user['sub']
    rating_id = str(uuid.uuid4())
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        # Check if recipe exists and belongs to user
        result = session.execute(text("SELECT id, name FROM saved_recipes WHERE id = :recipe_id AND user_id = :user_id"), 
                               {"recipe_id": recipe_id, "user_id": user_id})
        recipe = result.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Insert new rating
        session.execute(text('''
            INSERT INTO recipe_ratings 
            (id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes)
            VALUES (:rating_id, :recipe_id, :user_id, :rating, :review_text, :would_make_again, :cooking_notes)
        '''), {
            'rating_id': rating_id, 'recipe_id': recipe_id, 'user_id': user_id, 'rating': rating_data.rating,
            'review_text': rating_data.review_text, 'would_make_again': rating_data.would_make_again, 'cooking_notes': rating_data.cooking_notes
        })
        
        # Update recipe last_cooked timestamp
        session.execute(text(
            "UPDATE saved_recipes SET last_cooked = CURRENT_TIMESTAMP, times_cooked = times_cooked + 1 WHERE id = :recipe_id"
        ), {'recipe_id': recipe_id})
        
        # Get the created rating
        result = session.execute(text('''
            SELECT id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes, created_at
            FROM recipe_ratings WHERE id = :rating_id
        '''), {"rating_id": rating_id})
        rating = result.fetchone()
        
        if not rating:
            raise HTTPException(status_code=500, detail="Rating was not saved properly")
        
        logger.info(f"✅ Recipe rated successfully: {rating_id}")
        
        return RecipeRatingResponse(
            id=str(rating[0]),
            recipe_id=str(rating[1]),
            user_id=str(rating[2]),
            rating=rating[3],
            review_text=rating[4],
            would_make_again=bool(rating[5]),
            cooking_notes=rating[6],
            created_at=rating[7].isoformat() if rating[7] else None
        )


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, authorization: str = Header(None)):
    """Delete a saved recipe"""
    logger.info(f"🗑️ Delete recipe request: {recipe_id}")
    
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        # Check if recipe exists and belongs to user
        result = session.execute(text("""
            SELECT id, name FROM saved_recipes 
            WHERE id = :recipe_id AND user_id = :user_id
        """), {"recipe_id": recipe_id, "user_id": user_id})
        recipe = result.fetchone()
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        recipe_name = recipe[1]
        
        # Delete associated ratings first (foreign key constraint)
        session.execute(text("""
            DELETE FROM recipe_ratings 
            WHERE recipe_id = :recipe_id
        """), {"recipe_id": recipe_id})
        logger.info(f"🗑️ Deleted ratings for recipe: {recipe_name}")
        
        # Delete the recipe
        result = session.execute(text("""
            DELETE FROM saved_recipes 
            WHERE id = :recipe_id AND user_id = :user_id
        """), {"recipe_id": recipe_id, "user_id": user_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recipe not found or already deleted")
        
        logger.info(f"✅ Recipe deleted successfully: {recipe_name}")
        
        return {"message": f"Recipe '{recipe_name}' deleted successfully"}