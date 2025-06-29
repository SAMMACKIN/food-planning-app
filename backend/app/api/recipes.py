"""
Saved recipes API endpoints
"""
import sqlite3
import datetime
import logging
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from ..core.database import get_db_connection, get_db_cursor
from ..core.security import verify_token
from ..schemas.meals import (
    SavedRecipeCreate, SavedRecipeUpdate, SavedRecipeResponse,
    RecipeRatingCreate, RecipeRatingUpdate, RecipeRatingResponse
)

router = APIRouter(tags=["recipes"])
logger = logging.getLogger(__name__)


def get_current_user(authorization: str = None):
    """Get current user with improved error handling and logging"""
    logger.debug(f"🔐 Authentication check - Authorization header present: {bool(authorization)}")
    
    if not authorization:
        logger.warning("❌ No authorization header provided")
        return None
    
    if not authorization.startswith("Bearer "):
        logger.warning(f"❌ Invalid authorization header format: {authorization[:20]}...")
        return None
    
    try:
        token = authorization.split(" ")[1]
        logger.debug(f"🔑 Extracted token length: {len(token)}")
        
        payload = verify_token(token)
        logger.debug(f"🔓 Token verification result: {bool(payload)}")
        
        if payload and 'sub' in payload:
            user_id = payload['sub']
            logger.debug(f"✅ Authentication successful for user: {user_id}")
            return payload
        else:
            logger.warning("❌ Token payload missing 'sub' field")
            return None
            
    except Exception as e:
        logger.error(f"❌ Token processing error: {e}")
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
    logger.info(f"🍽️ Authorization header present: {bool(authorization)}")
    logger.info(f"🍽️ Search: {search}, Difficulty: {difficulty}, Tags: {tags}")
    
    try:
        current_user = get_current_user(authorization)
        logger.info(f"🍽️ Authentication result: {bool(current_user)}")
        if current_user:
            logger.info(f"🍽️ User ID: {current_user.get('sub', 'NO_ID')}")
    except Exception as e:
        logger.error(f"🍽️ Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
    
    if not current_user:
        logger.error("🍽️ Authentication failed - no current user")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        logger.info("🍽️ Getting database connection...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("🍽️ Database connection successful")
    except Exception as e:
        logger.error(f"🍽️ Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    
    try:
        user_id = current_user['sub']
        logger.info(f"🍽️ Processing request for user: {user_id}")
        
        # Base query
        logger.info("🍽️ Building query...")
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
        logger.info(f"🍽️ Base query: {query[:100]}...")
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
        
        logger.info(f"🍽️ Final query: {query}")
        logger.info(f"🍽️ Query params: {params}")
        logger.info("🍽️ Executing query...")
        
        cursor.execute(query, params)
        recipes_data = cursor.fetchall()
        logger.info(f"🍽️ Found {len(recipes_data)} recipes")
        
        recipes = []
        for recipe in recipes_data:
            try:
                ingredients_needed = json.loads(recipe[7]) if recipe[7] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    try:
                        ingredients_needed = json.loads(recipe[7]) if recipe[7] else []
                    except (json.JSONDecodeError, TypeError):
                        ingredients_needed = []
                except:
                    ingredients_needed = []
            
            try:
                instructions = json.loads(recipe[8]) if recipe[8] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    try:
                        instructions = json.loads(recipe[8]) if recipe[8] else []
                    except (json.JSONDecodeError, TypeError):
                        instructions = []
                except:
                    instructions = []
            
            try:
                tags = json.loads(recipe[9]) if recipe[9] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    try:
                        tags = json.loads(recipe[9]) if recipe[9] else []
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                except:
                    tags = []
            
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
                tags=tags,
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
        
    except Exception as e:
        logger.error(f"Error fetching saved recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching saved recipes: {str(e)}")
    
    finally:
        conn.close()


@router.post("", response_model=SavedRecipeResponse)
async def save_recipe(recipe_data: SavedRecipeCreate, authorization: str = Header(None)):
    """Save a new recipe with improved error handling"""
    logger.info(f"🍽️ Recipe save request: {recipe_data.name}")
    
    current_user = get_current_user(authorization)
    if not current_user:
        logger.warning("❌ Recipe save failed: Authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['sub']
    recipe_id = str(uuid.uuid4())
    
    logger.info(f"👤 Saving recipe for user: {user_id}")
    logger.info(f"📝 Recipe details: {recipe_data.name} ({recipe_data.difficulty}, {recipe_data.prep_time}min)")
    
    try:
        with get_db_cursor() as (cursor, conn):
            # Validate required fields
            if not recipe_data.name or not recipe_data.description:
                raise HTTPException(status_code=400, detail="Recipe name and description are required")
            
            if recipe_data.prep_time <= 0 or recipe_data.servings <= 0:
                raise HTTPException(status_code=400, detail="Prep time and servings must be positive numbers")
            
            # Insert new saved recipe
            logger.debug(f"💾 Inserting recipe into database...")
            cursor.execute('''
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
            
            logger.debug(f"✅ Recipe inserted successfully")
            
            # Get the created recipe
            cursor.execute('''
                SELECT id, user_id, name, description, prep_time, difficulty, servings, 
                       ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
                       ai_generated, ai_provider, source, times_cooked, last_cooked, created_at, updated_at
                FROM saved_recipes WHERE id = ?
            ''', (recipe_id,))
            recipe = cursor.fetchone()
            
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
        
    except HTTPException:
        raise
    except sqlite3.OperationalError as e:
        logger.error(f"❌ Database operational error saving recipe: {e}")
        if "no such table" in str(e).lower():
            raise HTTPException(status_code=500, detail="Database schema error: saved_recipes table missing. Please restart the application to repair the database schema.")
        elif "no such column" in str(e).lower():
            raise HTTPException(status_code=500, detail="Database schema error: recipe table columns missing. Please restart the application to repair the database schema.")
        else:
            raise HTTPException(status_code=500, detail=f"Database operational error: {str(e)}")
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Database integrity error saving recipe: {e}")
        raise HTTPException(status_code=400, detail="Recipe data violates database constraints")
    except json.JSONEncodeError as e:
        logger.error(f"❌ JSON encoding error saving recipe: {e}")
        raise HTTPException(status_code=400, detail="Invalid recipe data format")
    except Exception as e:
        logger.error(f"❌ Unexpected error saving recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving recipe: {str(e)}")


@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_saved_recipe(recipe_id: str, authorization: str = Header(None)):
    """Get a specific saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        cursor.execute('''
            SELECT r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                   r.servings, r.ingredients_needed, r.instructions, r.tags, r.nutrition_notes,
                   r.pantry_usage_score, r.ai_generated, r.ai_provider, r.source,
                   r.times_cooked, r.last_cooked, r.created_at, r.updated_at,
                   AVG(rt.rating) as avg_rating
            FROM saved_recipes r
            LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
            WHERE r.id = ? AND r.user_id = ?
            GROUP BY r.id
        ''', (recipe_id, user_id))
        
        recipe = cursor.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
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
            rating=float(recipe[19]) if recipe[19] else None,
            created_at=recipe[17],
            updated_at=recipe[18]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recipe: {str(e)}")
    
    finally:
        conn.close()


@router.put("/{recipe_id}", response_model=SavedRecipeResponse)
async def update_saved_recipe(
    recipe_id: str, 
    recipe_data: SavedRecipeUpdate, 
    authorization: str = Header(None)
):
    """Update a saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if recipe exists and belongs to user
        cursor.execute(
            "SELECT id FROM saved_recipes WHERE id = ? AND user_id = ?", 
            (recipe_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Build update query dynamically
        updates = []
        values = []
        
        if recipe_data.name is not None:
            updates.append("name = ?")
            values.append(recipe_data.name)
        if recipe_data.description is not None:
            updates.append("description = ?")
            values.append(recipe_data.description)
        if recipe_data.prep_time is not None:
            updates.append("prep_time = ?")
            values.append(recipe_data.prep_time)
        if recipe_data.difficulty is not None:
            updates.append("difficulty = ?")
            values.append(recipe_data.difficulty)
        if recipe_data.servings is not None:
            updates.append("servings = ?")
            values.append(recipe_data.servings)
        if recipe_data.ingredients_needed is not None:
            updates.append("ingredients_needed = ?")
            values.append(json.dumps(recipe_data.ingredients_needed))
        if recipe_data.instructions is not None:
            updates.append("instructions = ?")
            values.append(json.dumps(recipe_data.instructions))
        if recipe_data.tags is not None:
            updates.append("tags = ?")
            values.append(json.dumps(recipe_data.tags))
        if recipe_data.nutrition_notes is not None:
            updates.append("nutrition_notes = ?")
            values.append(recipe_data.nutrition_notes)
        if recipe_data.pantry_usage_score is not None:
            updates.append("pantry_usage_score = ?")
            values.append(recipe_data.pantry_usage_score)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.extend([recipe_id, user_id])
            cursor.execute(
                f"UPDATE saved_recipes SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
                values
            )
            conn.commit()
        
        # Get updated recipe
        return await get_saved_recipe(recipe_id, authorization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating recipe: {str(e)}")
    
    finally:
        conn.close()


@router.delete("/{recipe_id}")
async def delete_saved_recipe(recipe_id: str, authorization: str = Header(None)):
    """Delete a saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if recipe exists and belongs to user
        cursor.execute(
            "SELECT id FROM saved_recipes WHERE id = ? AND user_id = ?", 
            (recipe_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Delete recipe ratings first (foreign key constraint)
        cursor.execute("DELETE FROM recipe_ratings WHERE recipe_id = ?", (recipe_id,))
        
        # Delete the recipe
        cursor.execute(
            "DELETE FROM saved_recipes WHERE id = ? AND user_id = ?", 
            (recipe_id, user_id)
        )
        conn.commit()
        
        return {"message": "Recipe deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting recipe: {str(e)}")
    
    finally:
        conn.close()


@router.post("/{recipe_id}/ratings", response_model=RecipeRatingResponse)
async def rate_recipe(
    recipe_id: str, 
    rating_data: RecipeRatingCreate, 
    authorization: str = Header(None)
):
    """Rate a saved recipe with improved error handling"""
    logger.info(f"⭐ Recipe rating request: {recipe_id} with {rating_data.rating} stars")
    
    current_user = get_current_user(authorization)
    if not current_user:
        logger.warning("❌ Recipe rating failed: Authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if rating_data.rating < 1 or rating_data.rating > 5:
        logger.warning(f"❌ Invalid rating value: {rating_data.rating}")
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    user_id = current_user['sub']
    rating_id = str(uuid.uuid4())
    
    logger.info(f"👤 Rating recipe for user: {user_id}")
    
    try:
        with get_db_cursor() as (cursor, conn):
            # Check if recipe exists and belongs to user
            cursor.execute(
                "SELECT id, name FROM saved_recipes WHERE id = ? AND user_id = ?", 
                (recipe_id, user_id)
            )
            recipe = cursor.fetchone()
            if not recipe:
                logger.warning(f"❌ Recipe not found: {recipe_id} for user: {user_id}")
                raise HTTPException(status_code=404, detail="Recipe not found")
            
            logger.debug(f"📝 Rating recipe: {recipe[1]}")
            
            # Insert new rating
            cursor.execute('''
                INSERT INTO recipe_ratings 
                (id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                rating_id, recipe_id, user_id, rating_data.rating,
                rating_data.review_text, rating_data.would_make_again, rating_data.cooking_notes
            ))
            
            logger.debug(f"✅ Rating inserted successfully")
            
            # Update recipe last_cooked timestamp
            cursor.execute(
                "UPDATE saved_recipes SET last_cooked = CURRENT_TIMESTAMP, times_cooked = times_cooked + 1 WHERE id = ?",
                (recipe_id,)
            )
            
            logger.debug(f"✅ Recipe stats updated")
            
            # Get the created rating
            cursor.execute('''
                SELECT id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes, created_at
                FROM recipe_ratings WHERE id = ?
            ''', (rating_id,))
            rating = cursor.fetchone()
            
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
        
    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Database integrity error rating recipe: {e}")
        raise HTTPException(status_code=400, detail="Rating data violates database constraints")
    except Exception as e:
        logger.error(f"❌ Unexpected error rating recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error rating recipe: {str(e)}")


@router.get("/{recipe_id}/ratings", response_model=List[RecipeRatingResponse])
async def get_recipe_ratings(recipe_id: str, authorization: str = Header(None)):
    """Get ratings for a recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if recipe exists and belongs to user
        cursor.execute(
            "SELECT id FROM saved_recipes WHERE id = ? AND user_id = ?", 
            (recipe_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        cursor.execute('''
            SELECT id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes, created_at
            FROM recipe_ratings 
            WHERE recipe_id = ?
            ORDER BY created_at DESC
        ''', (recipe_id,))
        
        ratings = cursor.fetchall()
        
        return [
            RecipeRatingResponse(
                id=rating[0],
                recipe_id=rating[1],
                user_id=rating[2],
                rating=rating[3],
                review_text=rating[4],
                would_make_again=bool(rating[5]),
                cooking_notes=rating[6],
                created_at=rating[7]
            )
            for rating in ratings
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe ratings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recipe ratings: {str(e)}")
    
    finally:
        conn.close()


@router.post("/{recipe_id}/add-to-meal-plan")
async def add_recipe_to_meal_plan(
    recipe_id: str,
    meal_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    meal_type: str = Query(..., description="breakfast, lunch, dinner, or snack"),
    authorization: str = Header(None)
):
    """Add a saved recipe to meal plan with improved error handling"""
    logger.info(f"📅 Add to meal plan request: {recipe_id} for {meal_date} {meal_type}")
    
    current_user = get_current_user(authorization)
    if not current_user:
        logger.warning("❌ Add to meal plan failed: Authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if meal_type not in ['breakfast', 'lunch', 'dinner', 'snack']:
        logger.warning(f"❌ Invalid meal type: {meal_type}")
        raise HTTPException(status_code=400, detail="Invalid meal type")
    
    # Validate date format
    try:
        datetime.strptime(meal_date, '%Y-%m-%d')
    except ValueError:
        logger.warning(f"❌ Invalid date format: {meal_date}")
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")
    
    user_id = current_user['sub']
    meal_plan_id = str(uuid.uuid4())
    
    logger.info(f"👤 Adding to meal plan for user: {user_id}")
    
    try:
        with get_db_cursor() as (cursor, conn):
            # Get the recipe
            cursor.execute('''
                SELECT name, description, prep_time, difficulty, servings, ingredients_needed, 
                       instructions, tags, nutrition_notes, ai_generated, ai_provider
                FROM saved_recipes WHERE id = ? AND user_id = ?
            ''', (recipe_id, user_id))
            
            recipe = cursor.fetchone()
            if not recipe:
                logger.warning(f"❌ Recipe not found: {recipe_id} for user: {user_id}")
                raise HTTPException(status_code=404, detail="Recipe not found")
            
            logger.debug(f"📝 Adding recipe to meal plan: {recipe[0]}")
            
            # Check if meal already exists for this slot
            cursor.execute(
                "SELECT id FROM meal_plans WHERE user_id = ? AND date = ? AND meal_type = ?",
                (user_id, meal_date, meal_type)
            )
            existing_meal = cursor.fetchone()
            if existing_meal:
                logger.warning(f"❌ Meal slot already occupied: {meal_date} {meal_type}")
                raise HTTPException(status_code=400, detail="Meal already planned for this time slot")
            
            # Create recipe data object
            recipe_data = {
                "name": recipe[0],
                "description": recipe[1],
                "prep_time": recipe[2],
                "difficulty": recipe[3],
                "servings": recipe[4],
                "ingredients_needed": json.loads(recipe[5]) if recipe[5] else [],
                "instructions": json.loads(recipe[6]) if recipe[6] else [],
                "tags": json.loads(recipe[7]) if recipe[7] else [],
                "nutrition_notes": recipe[8],
                "saved_recipe_id": recipe_id
            }
            
            # Insert into meal plans
            cursor.execute('''
                INSERT INTO meal_plans 
                (id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meal_plan_id, user_id, meal_date, meal_type, recipe[0], recipe[1],
                json.dumps(recipe_data), recipe[9] or False, recipe[10]
            ))
            
            logger.info(f"✅ Recipe added to meal plan successfully: {meal_plan_id}")
            
            return {
                "message": "Recipe added to meal plan successfully",
                "meal_plan_id": meal_plan_id,
                "date": meal_date,
                "meal_type": meal_type,
                "recipe_name": recipe[0]
            }
        
    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Database integrity error adding to meal plan: {e}")
        raise HTTPException(status_code=400, detail="Meal plan data violates database constraints")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON encoding error adding to meal plan: {e}")
        raise HTTPException(status_code=500, detail="Error processing recipe data")
    except Exception as e:
        logger.error(f"❌ Unexpected error adding recipe to meal plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding recipe to meal plan: {str(e)}")


@router.get("/debug/health")
async def debug_recipes_health(authorization: str = Header(None)):
    """Debug endpoint to test recipe system health"""
    logger.info("🔍 Recipe system health check requested")
    
    current_user = get_current_user(authorization)
    if not current_user:
        return {"status": "error", "message": "Authentication required"}
    
    user_id = current_user['sub']
    health_status = {
        "status": "healthy",
        "user_id": user_id,
        "database": "unknown",
        "tables": {},
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    try:
        with get_db_cursor() as (cursor, conn):
            # Test database connection
            cursor.execute("SELECT 1")
            health_status["database"] = "connected"
            
            # Check table counts
            tables_to_check = ['users', 'saved_recipes', 'recipe_ratings', 'meal_plans']
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    health_status["tables"][table] = {"exists": True, "count": count}
                except Exception as e:
                    health_status["tables"][table] = {"exists": False, "error": str(e)}
            
            # Test user-specific data
            cursor.execute("SELECT COUNT(*) FROM saved_recipes WHERE user_id = ?", (user_id,))
            user_recipes = cursor.fetchone()[0]
            health_status["user_data"] = {"recipes": user_recipes}
            
        logger.info(f"✅ Recipe system health check completed successfully")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Recipe system health check failed: {e}")
        health_status["status"] = "error"
        health_status["error"] = str(e)
        return health_status