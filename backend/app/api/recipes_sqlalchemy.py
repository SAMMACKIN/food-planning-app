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
        if db_service.use_sqlite:
            # SQLite query
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
            
        else:
            # SQLAlchemy query
            query = session.query(
                SavedRecipe,
                func.avg(RecipeRating.rating).label('avg_rating')
            ).outerjoin(RecipeRating).filter(SavedRecipe.user_id == user_id)
            
            # Add filters
            if search:
                search_term = f'%{search}%'
                query = query.filter(
                    (SavedRecipe.name.like(search_term)) |
                    (SavedRecipe.description.like(search_term)) |
                    (SavedRecipe.tags.like(search_term))
                )
            
            if difficulty:
                query = query.filter(SavedRecipe.difficulty == difficulty)
            
            if tags:
                query = query.filter(SavedRecipe.tags.like(f'%{tags}%'))
            
            query = query.group_by(SavedRecipe.id).order_by(SavedRecipe.updated_at.desc())
            recipes_data = query.all()
        
        recipes = []
        for recipe_data in recipes_data:
            if db_service.use_sqlite:
                # SQLite result processing
                recipe = recipe_data
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
            else:
                # SQLAlchemy result processing
                recipe, avg_rating = recipe_data
                
                try:
                    ingredients_needed = json.loads(recipe.ingredients_needed) if recipe.ingredients_needed else []
                except (json.JSONDecodeError, TypeError):
                    ingredients_needed = []
                
                try:
                    instructions = json.loads(recipe.instructions) if recipe.instructions else []
                except (json.JSONDecodeError, TypeError):
                    instructions = []
                
                try:
                    tags_list = json.loads(recipe.tags) if recipe.tags else []
                except (json.JSONDecodeError, TypeError):
                    tags_list = []
                
                recipes.append(SavedRecipeResponse(
                    id=recipe.id,
                    user_id=recipe.user_id,
                    name=recipe.name,
                    description=recipe.description,
                    prep_time=recipe.prep_time,
                    difficulty=recipe.difficulty,
                    servings=recipe.servings,
                    ingredients_needed=ingredients_needed,
                    instructions=instructions,
                    tags=tags_list,
                    nutrition_notes=recipe.nutrition_notes,
                    pantry_usage_score=recipe.pantry_usage_score,
                    ai_generated=recipe.ai_generated,
                    ai_provider=recipe.ai_provider,
                    source=recipe.source,
                    times_cooked=recipe.times_cooked or 0,
                    last_cooked=recipe.last_cooked,
                    rating=float(avg_rating) if avg_rating else None,
                    created_at=recipe.created_at,
                    updated_at=recipe.updated_at
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
        if db_service.use_sqlite:
            # SQLite insert
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
            
        else:
            # SQLAlchemy insert
            new_recipe = SavedRecipe(
                id=recipe_id,
                user_id=user_id,
                name=recipe_data.name,
                description=recipe_data.description,
                prep_time=recipe_data.prep_time,
                difficulty=recipe_data.difficulty,
                servings=recipe_data.servings,
                ingredients_needed=json.dumps(recipe_data.ingredients_needed),
                instructions=json.dumps(recipe_data.instructions),
                tags=json.dumps(recipe_data.tags),
                nutrition_notes=recipe_data.nutrition_notes,
                pantry_usage_score=recipe_data.pantry_usage_score,
                ai_generated=recipe_data.ai_generated,
                ai_provider=recipe_data.ai_provider,
                source=recipe_data.source
            )
            session.add(new_recipe)
            session.flush()  # Get the ID
            recipe = new_recipe
        
        if not recipe:
            raise HTTPException(status_code=500, detail="Recipe was not saved properly")
        
        if db_service.use_sqlite:
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
        else:
            return SavedRecipeResponse(
                id=recipe.id,
                user_id=recipe.user_id,
                name=recipe.name,
                description=recipe.description,
                prep_time=recipe.prep_time,
                difficulty=recipe.difficulty,
                servings=recipe.servings,
                ingredients_needed=json.loads(recipe.ingredients_needed) if recipe.ingredients_needed else [],
                instructions=json.loads(recipe.instructions) if recipe.instructions else [],
                tags=json.loads(recipe.tags) if recipe.tags else [],
                nutrition_notes=recipe.nutrition_notes,
                pantry_usage_score=recipe.pantry_usage_score,
                ai_generated=recipe.ai_generated,
                ai_provider=recipe.ai_provider,
                source=recipe.source,
                times_cooked=recipe.times_cooked or 0,
                last_cooked=recipe.last_cooked,
                rating=None,
                created_at=recipe.created_at,
                updated_at=recipe.updated_at
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
        if db_service.use_sqlite:
            # Check if recipe exists
            session.execute("SELECT id, name FROM saved_recipes WHERE id = ? AND user_id = ?", (recipe_id, user_id))
            recipe = session.fetchone()
            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")
            
            # Insert rating
            session.execute('''
                INSERT INTO recipe_ratings 
                (id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rating_id, recipe_id, user_id, rating_data.rating,
                  rating_data.review_text, rating_data.would_make_again, rating_data.cooking_notes))
            
            # Update recipe stats
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
            
        else:
            # Check if recipe exists
            recipe = session.query(SavedRecipe).filter(
                SavedRecipe.id == recipe_id,
                SavedRecipe.user_id == user_id
            ).first()
            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")
            
            # Create rating
            new_rating = RecipeRating(
                id=rating_id,
                recipe_id=recipe_id,
                user_id=user_id,
                rating=rating_data.rating,
                review_text=rating_data.review_text,
                would_make_again=rating_data.would_make_again,
                cooking_notes=rating_data.cooking_notes
            )
            session.add(new_rating)
            
            # Update recipe stats
            recipe.times_cooked = (recipe.times_cooked or 0) + 1
            recipe.last_cooked = func.current_timestamp()
            
            session.flush()
            rating = new_rating
        
        if not rating:
            raise HTTPException(status_code=500, detail="Rating was not saved properly")
        
        if db_service.use_sqlite:
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
        else:
            return RecipeRatingResponse(
                id=rating.id,
                recipe_id=rating.recipe_id,
                user_id=rating.user_id,
                rating=rating.rating,
                review_text=rating.review_text,
                would_make_again=rating.would_make_again,
                cooking_notes=rating.cooking_notes,
                created_at=rating.created_at
            )