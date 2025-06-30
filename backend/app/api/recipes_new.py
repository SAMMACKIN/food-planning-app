"""
Saved recipes API endpoints - SQLAlchemy version
"""
import logging
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..models.simple_models import SavedRecipe, RecipeRating, User
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
    logger.info("🍽️ GET SAVED RECIPES ENDPOINT CALLED")
    
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    
    with get_db_session() as session:
        # Use SQLite for now (unified approach)
        query = '''
            SELECT r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                   r.servings, r.ingredients_needed, r.instructions, r.tags, r.nutrition_notes,
                   r.pantry_usage_score, r.ai_generated, r.ai_provider, r.source,
                   r.times_cooked, r.last_cooked, r.created_at, r.updated_at,
                   AVG(rt.rating) as avg_rating
            FROM saved_recipes r
            LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
            WHERE r.user_id = ?
        '''
        params = [user_id]
        
        # Add search filter
        if search:
            query += ' AND (r.name LIKE ? OR r.description LIKE ? OR r.tags LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        # Add difficulty filter
        if difficulty:
            query += ' AND r.difficulty = ?'
            params.append(difficulty)
        
        # Add tags filter
        if tags:
            query += ' AND r.tags LIKE ?'
            params.append(f'%{tags}%')
        
        query += ' GROUP BY r.id ORDER BY r.updated_at DESC'
        
        session.execute(query, params)
        recipes_data = session.fetchall()
        
        recipes = []
        for recipe in recipes_data:
            try:
                ingredients_needed = json.loads(recipe[7]) if recipe[7] else []
            except (json.JSONDecodeError, TypeError):
                ingredients_needed = []
            
            try:
                instructions = json.loads(recipe[8]) if recipe[8] else []
            except (json.JSONDecodeError, TypeError):
                instructions = []
            
            try:
                tags_list = json.loads(recipe[9]) if recipe[9] else []
            except (json.JSONDecodeError, TypeError):
                tags_list = []
            
            recipes.append(SavedRecipeResponse(
                id=recipe[0],
                user_id=recipe[1],
                name=recipe[2],
                description=recipe[3],
                prep_time=recipe[4],
                difficulty=recipe[5],
                servings=recipe[6],
                ingredients_needed=ingredients_needed,
                instructions=instructions,
                tags=tags_list,
                nutrition_notes=recipe[10],
                pantry_usage_score=recipe[11],
                ai_generated=bool(recipe[12]),
                ai_provider=recipe[13],
                source=recipe[14],
                times_cooked=recipe[15] or 0,
                last_cooked=recipe[16],
                rating=float(recipe[19]) if recipe[19] else None,
                created_at=recipe[17],
                updated_at=recipe[18]
            ))
        
        return recipes


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
        # Validate required fields
        if not recipe_data.name or not recipe_data.description:
            raise HTTPException(status_code=400, detail="Recipe name and description are required")
        
        if recipe_data.prep_time <= 0 or recipe_data.servings <= 0:
            raise HTTPException(status_code=400, detail="Prep time and servings must be positive numbers")
        
        # Insert new saved recipe
        session.execute('''
            INSERT INTO saved_recipes 
            (id, user_id, name, description, prep_time, difficulty, servings, 
             ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
             ai_generated, ai_provider, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipe_id, user_id, recipe_data.name, recipe_data.description,
            recipe_data.prep_time, recipe_data.difficulty, recipe_data.servings,
            json.dumps(recipe_data.ingredients_needed), 
            json.dumps(recipe_data.instructions),
            json.dumps(recipe_data.tags),
            recipe_data.nutrition_notes, recipe_data.pantry_usage_score,
            recipe_data.ai_generated, recipe_data.ai_provider, recipe_data.source
        ))
        
        # Get the created recipe
        session.execute('''
            SELECT id, user_id, name, description, prep_time, difficulty, servings, 
                   ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
                   ai_generated, ai_provider, source, times_cooked, last_cooked, created_at, updated_at
            FROM saved_recipes WHERE id = ?
        ''', (recipe_id,))
        recipe = session.fetchone()
        
        if not recipe:
            raise HTTPException(status_code=500, detail="Recipe was not saved properly")
        
        logger.info(f"✅ Recipe saved successfully: {recipe_id}")
        
        return SavedRecipeResponse(
            id=recipe[0],
            user_id=recipe[1],
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
            last_cooked=recipe[16],
            rating=None,
            created_at=recipe[17],
            updated_at=recipe[18]
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
        # Check if recipe exists and belongs to user
        session.execute("SELECT id, name FROM saved_recipes WHERE id = ? AND user_id = ?", (recipe_id, user_id))
        recipe = session.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Insert new rating
        session.execute('''
            INSERT INTO recipe_ratings 
            (id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rating_id, recipe_id, user_id, rating_data.rating,
            rating_data.review_text, rating_data.would_make_again, rating_data.cooking_notes
        ))
        
        # Update recipe last_cooked timestamp
        session.execute(
            "UPDATE saved_recipes SET last_cooked = CURRENT_TIMESTAMP, times_cooked = times_cooked + 1 WHERE id = ?",
            (recipe_id,)
        )
        
        # Get the created rating
        session.execute('''
            SELECT id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes, created_at
            FROM recipe_ratings WHERE id = ?
        ''', (rating_id,))
        rating = session.fetchone()
        
        if not rating:
            raise HTTPException(status_code=500, detail="Rating was not saved properly")
        
        logger.info(f"✅ Recipe rated successfully: {rating_id}")
        
        return RecipeRatingResponse(
            id=rating[0],
            recipe_id=rating[1],
            user_id=rating[2],
            rating=rating[3],
            review_text=rating[4],
            would_make_again=bool(rating[5]),
            cooking_notes=rating[6],
            created_at=rating[7]
        )