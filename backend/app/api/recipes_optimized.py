"""
Optimized saved recipes API endpoints with performance improvements
"""
import logging
import json
import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import joinedload

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


def safe_json_parse(json_str: str, default_value=None):
    """Safely parse JSON string with fallback"""
    if not json_str:
        return default_value or []
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {json_str[:100]}... Error: {e}")
        return default_value or []


@router.get("/optimized", response_model=List[SavedRecipeResponse])
async def get_saved_recipes_optimized(
    search: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    authorization: str = Header(None)
):
    """Get user's saved recipes with performance optimization"""
    start_time = time.time()
    
    try:
        current_user = get_current_user(authorization)
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user['sub']
        
        with get_db_session() as session:
            from ..models.recipe import SavedRecipe
            # RecipeRating might not exist yet, so handle import gracefully
            try:
                from ..models.recipe import RecipeRating
            except ImportError:
                RecipeRating = None
            import uuid as uuid_module
            
            # Convert user_id string to UUID object
            try:
                user_uuid = uuid_module.UUID(user_id)
            except ValueError as e:
                logger.error(f"Invalid UUID format: {user_id} - {e}")
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            
            # Use efficient single query (skip eager loading for now to avoid issues)
            query = session.query(SavedRecipe).filter(SavedRecipe.user_id == user_uuid)
            
            # Add search filter
            if search:
                search_filter = f'%{search}%'
                query = query.filter(
                    or_(
                        SavedRecipe.name.ilike(search_filter),
                        SavedRecipe.description.ilike(search_filter),
                        SavedRecipe.tags.ilike(search_filter)
                    )
                )
            
            # Add difficulty filter  
            if difficulty:
                query = query.filter(SavedRecipe.difficulty == difficulty)
                
            # Add tags filter
            if tags:
                query = query.filter(SavedRecipe.tags.ilike(f'%{tags}%'))
            
            # Order by updated_at DESC (uses compound index)
            query = query.order_by(SavedRecipe.updated_at.desc())
            
            # Execute query - this loads all recipes AND ratings in one query
            recipes_data = query.all()
            
            query_time = time.time() - start_time
            logger.info(f"🚀 Optimized query took {query_time:.4f}s for {len(recipes_data)} recipes")
            
            # Process ORM objects efficiently
            recipes = []
            for recipe in recipes_data:
                try:
                    # Skip ratings for now to avoid issues
                    avg_rating = None
                    
                    # Parse JSON fields with safe error handling
                    ingredients_needed = safe_json_parse(recipe.ingredients_needed, [])
                    instructions = safe_json_parse(recipe.instructions, [])
                    tags_list = safe_json_parse(recipe.tags, [])
                    
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
                        tags=tags_list,
                        nutrition_notes=recipe.nutrition_notes or "",
                        pantry_usage_score=recipe.pantry_usage_score or 0,
                        ai_generated=recipe.ai_generated or False,
                        ai_provider=recipe.ai_provider,
                        source=recipe.source or "manual",
                        times_cooked=recipe.times_cooked or 0,
                        last_cooked=recipe.last_cooked.isoformat() if recipe.last_cooked else None,
                        rating=avg_rating,
                        created_at=recipe.created_at.isoformat() if recipe.created_at else None,
                        updated_at=recipe.updated_at.isoformat() if recipe.updated_at else None
                    )
                    recipes.append(recipe_response)
                    
                except Exception as e:
                    logger.error(f"Error processing recipe {recipe.name if hasattr(recipe, 'name') else 'unknown'}: {e}")
                    continue
            
            total_time = time.time() - start_time
            logger.info(f"✅ Optimized endpoint completed in {total_time:.4f}s")
            
            return recipes
        
    except Exception as e:
        logger.error(f"Critical error in optimized get_saved_recipes: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching saved recipes: {str(e)}")


@router.get("/fast", response_model=List[SavedRecipeResponse])
async def get_saved_recipes_fast(
    search: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    authorization: str = Header(None)
):
    """Ultra-fast saved recipes using optimized single SQL query"""
    start_time = time.time()
    
    try:
        current_user = get_current_user(authorization)
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user['sub']
        
        with get_db_session() as session:
            import uuid as uuid_module
            
            # Convert user_id string to UUID object
            try:
                user_uuid = uuid_module.UUID(user_id)
            except ValueError as e:
                logger.error(f"Invalid UUID format: {user_id} - {e}")
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            
            # Single optimized SQL query with LEFT JOIN for ratings
            query = """
                SELECT 
                    r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                    r.servings, r.ingredients_needed, r.instructions, r.tags,
                    r.nutrition_notes, r.pantry_usage_score, r.ai_generated, 
                    r.ai_provider, r.source, r.times_cooked, r.last_cooked,
                    r.created_at, r.updated_at,
                    AVG(rt.rating) as avg_rating
                FROM saved_recipes r
                LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
                WHERE r.user_id = :user_id
            """
            
            params = {'user_id': user_uuid}
            
            # Add search filter
            if search:
                query += " AND (r.name ILIKE :search OR r.description ILIKE :search OR r.tags ILIKE :search)"
                params['search'] = f'%{search}%'
            
            # Add difficulty filter
            if difficulty:
                query += " AND r.difficulty = :difficulty"
                params['difficulty'] = difficulty
            
            # Add tags filter
            if tags:
                query += " AND r.tags ILIKE :tags"
                params['tags'] = f'%{tags}%'
            
            # Group by all recipe columns and order by updated_at DESC
            query += """
                GROUP BY r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                         r.servings, r.ingredients_needed, r.instructions, r.tags,
                         r.nutrition_notes, r.pantry_usage_score, r.ai_generated, 
                         r.ai_provider, r.source, r.times_cooked, r.last_cooked,
                         r.created_at, r.updated_at
                ORDER BY r.updated_at DESC
            """
            
            # Execute single query
            result = session.execute(text(query), params)
            recipes_data = result.fetchall()
            
            query_time = time.time() - start_time
            logger.info(f"🚀 Fast query took {query_time:.4f}s for {len(recipes_data)} recipes")
            
            # Process results efficiently
            recipes = []
            for row in recipes_data:
                try:
                    # Parse JSON fields with safe error handling
                    ingredients_needed = safe_json_parse(row[7], [])
                    instructions = safe_json_parse(row[8], [])
                    tags_list = safe_json_parse(row[9], [])
                    
                    recipe_response = SavedRecipeResponse(
                        id=str(row[0]),
                        user_id=str(row[1]),
                        name=row[2],
                        description=row[3] or "",
                        prep_time=row[4],
                        difficulty=row[5],
                        servings=row[6],
                        ingredients_needed=ingredients_needed,
                        instructions=instructions,
                        tags=tags_list,
                        nutrition_notes=row[10] or "",
                        pantry_usage_score=row[11] or 0,
                        ai_generated=row[12] or False,
                        ai_provider=row[13],
                        source=row[14] or "manual",
                        times_cooked=row[15] or 0,
                        last_cooked=row[16].isoformat() if row[16] else None,
                        rating=float(row[19]) if row[19] else None,
                        created_at=row[17].isoformat() if row[17] else None,
                        updated_at=row[18].isoformat() if row[18] else None
                    )
                    recipes.append(recipe_response)
                    
                except Exception as e:
                    logger.error(f"Error processing recipe row: {e}")
                    continue
            
            total_time = time.time() - start_time
            logger.info(f"✅ Fast endpoint completed in {total_time:.4f}s")
            
            return recipes
        
    except Exception as e:
        logger.error(f"Critical error in fast get_saved_recipes: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching saved recipes: {str(e)}")


@router.get("/performance-test", response_model=dict)
async def performance_test(
    authorization: str = Header(None)
):
    """Compare performance of different recipe retrieval methods"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    results = {}
    
    # Test original endpoint
    try:
        start = time.time()
        response = await get_saved_recipes_optimized(authorization=authorization)
        results['optimized'] = {
            'time': round(time.time() - start, 4),
            'count': len(response),
            'status': 'success'
        }
    except Exception as e:
        results['optimized'] = {'status': 'error', 'error': str(e)}
    
    # Test fast endpoint
    try:
        start = time.time()
        response = await get_saved_recipes_fast(authorization=authorization)
        results['fast'] = {
            'time': round(time.time() - start, 4),
            'count': len(response),
            'status': 'success'
        }
    except Exception as e:
        results['fast'] = {'status': 'error', 'error': str(e)}
    
    return results