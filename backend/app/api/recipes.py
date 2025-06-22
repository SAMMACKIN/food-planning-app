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

from ..core.database import get_db_connection
from ..core.security import verify_token
from ..schemas.meals import (
    SavedRecipeCreate, SavedRecipeUpdate, SavedRecipeResponse,
    RecipeRatingCreate, RecipeRatingUpdate, RecipeRatingResponse
)

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    return verify_token(token)


@router.get("", response_model=List[SavedRecipeResponse])
async def get_saved_recipes(
    search: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    authorization: str = Header(None)
):
    """Get user's saved recipes with optional filtering"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Base query
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
        
        cursor.execute(query, params)
        recipes_data = cursor.fetchall()
        
        recipes = []
        for recipe in recipes_data:
            try:
                ingredients_needed = json.loads(recipe[7]) if recipe[7] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    ingredients_needed = eval(recipe[7]) if recipe[7] else []
                except:
                    ingredients_needed = []
            
            try:
                instructions = json.loads(recipe[8]) if recipe[8] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    instructions = eval(recipe[8]) if recipe[8] else []
                except:
                    instructions = []
            
            try:
                tags = json.loads(recipe[9]) if recipe[9] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    tags = eval(recipe[9]) if recipe[9] else []
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
    """Save a new recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        recipe_id = str(uuid.uuid4())
        
        # Insert new saved recipe
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
        conn.commit()
        
        # Get the created recipe
        cursor.execute('''
            SELECT id, user_id, name, description, prep_time, difficulty, servings, 
                   ingredients_needed, instructions, tags, nutrition_notes, pantry_usage_score,
                   ai_generated, ai_provider, source, times_cooked, last_cooked, created_at, updated_at
            FROM saved_recipes WHERE id = ?
        ''', (recipe_id,))
        recipe = cursor.fetchone()
        
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
        
    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving recipe: {str(e)}")
    
    finally:
        conn.close()


@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_saved_recipe(recipe_id: str, authorization: str = Header(None)):
    """Get a specific saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
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
        user_id = current_user['id']
        
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
        user_id = current_user['id']
        
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
    """Rate a saved recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if rating_data.rating < 1 or rating_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Check if recipe exists and belongs to user
        cursor.execute(
            "SELECT id FROM saved_recipes WHERE id = ? AND user_id = ?", 
            (recipe_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        rating_id = str(uuid.uuid4())
        
        # Insert new rating
        cursor.execute('''
            INSERT INTO recipe_ratings 
            (id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rating_id, recipe_id, user_id, rating_data.rating,
            rating_data.review_text, rating_data.would_make_again, rating_data.cooking_notes
        ))
        
        # Update recipe last_cooked timestamp
        cursor.execute(
            "UPDATE saved_recipes SET last_cooked = CURRENT_TIMESTAMP, times_cooked = times_cooked + 1 WHERE id = ?",
            (recipe_id,)
        )
        
        conn.commit()
        
        # Get the created rating
        cursor.execute('''
            SELECT id, recipe_id, user_id, rating, review_text, would_make_again, cooking_notes, created_at
            FROM recipe_ratings WHERE id = ?
        ''', (rating_id,))
        rating = cursor.fetchone()
        
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
    except Exception as e:
        logger.error(f"Error rating recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rating recipe: {str(e)}")
    
    finally:
        conn.close()


@router.get("/{recipe_id}/ratings", response_model=List[RecipeRatingResponse])
async def get_recipe_ratings(recipe_id: str, authorization: str = Header(None)):
    """Get ratings for a recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
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
    """Add a saved recipe to meal plan"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if meal_type not in ['breakfast', 'lunch', 'dinner', 'snack']:
        raise HTTPException(status_code=400, detail="Invalid meal type")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Get the recipe
        cursor.execute('''
            SELECT name, description, prep_time, difficulty, servings, ingredients_needed, 
                   instructions, tags, nutrition_notes, ai_generated, ai_provider
            FROM saved_recipes WHERE id = ? AND user_id = ?
        ''', (recipe_id, user_id))
        
        recipe = cursor.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if meal already exists for this slot
        cursor.execute(
            "SELECT id FROM meal_plans WHERE user_id = ? AND date = ? AND meal_type = ?",
            (user_id, meal_date, meal_type)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Meal already planned for this time slot")
        
        meal_plan_id = str(uuid.uuid4())
        
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
            json.dumps(recipe_data), recipe[9], recipe[10]
        ))
        
        conn.commit()
        
        return {
            "message": "Recipe added to meal plan successfully",
            "meal_plan_id": meal_plan_id,
            "date": meal_date,
            "meal_type": meal_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding recipe to meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding recipe to meal plan: {str(e)}")
    
    finally:
        conn.close()