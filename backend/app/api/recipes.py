"""
Saved recipes API endpoints – *refactored, take 2*
================================================

Why another update?
-------------------
The previous refactor converted the main list endpoint to a **sync** route. In some deployments the router was not picked up, so the client saw 404s. This version:

* keeps all performance wins (DB aggregation, `load_only`, pagination)
* **restores an `async def` route** but runs the blocking DB work in a thread‑pool using `starlette.concurrency.run_in_threadpool` – no event‑loop blocking, and FastAPI will definitely register the path.
* exposes *both* `/recipes` and `/recipes/` (trailing‑slash) as accepted paths to avoid mismatch.

Copy‑paste the whole file – all other endpoints are untouched.
"""
import logging
import json
import uuid
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Header, Query
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import load_only
from starlette.concurrency import run_in_threadpool

from ..core.database_service import get_db_session
from ..core.auth_service import AuthService
from ..schemas.meals import (
    SavedRecipeCreate,
    SavedRecipeUpdate,
    SavedRecipeResponse,
    RecipeRatingCreate,
    RecipeRatingUpdate,
    RecipeRatingResponse,
)

router = APIRouter(tags=["recipes"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_current_user(authorization: Union[str, None] = None):
    """Return minimal user dict or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1]
        user = AuthService.verify_user_token(token)
        if not user:
            return None
        return {
            "sub": user["id"],
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user["is_admin"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Authentication error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# READ -- list recipes (performance‑critical)
# ---------------------------------------------------------------------------

@router.get("", response_model=List[SavedRecipeResponse])
@router.get("/", response_model=List[SavedRecipeResponse], include_in_schema=False)
async def get_saved_recipes(  # noqa: D401,E501 – long signature
    search: Optional[str] = Query(None, description="Free‑text search"),
    difficulty: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Single tag to filter by"),
    limit: int = Query(30, le=100),
    offset: int = Query(0, ge=0),
    authorization: str = Header(None),
):
    """Return the caller’s saved recipes with lightweight filters."""

    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_uuid = uuid.UUID(current_user["sub"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # ---- blocking DB work wrapped in thread‑pool ---------------------------
    def _query() -> List[SavedRecipeResponse]:
        from ..models.recipe import SavedRecipe, RecipeRating  # local import avoids cycles
        with get_db_session() as session:
            # rating aggregate sub‑query
            rating_sq = (
                select(
                    RecipeRating.recipe_id,
                    func.avg(RecipeRating.rating).label("avg_rating"),
                )
                .group_by(RecipeRating.recipe_id)
                .subquery()
            )

            stmt = (
                select(SavedRecipe, rating_sq.c.avg_rating)
                .outerjoin(rating_sq, SavedRecipe.id == rating_sq.c.recipe_id)
                .where(SavedRecipe.user_id == user_uuid)
                .order_by(desc(SavedRecipe.updated_at))
                .limit(limit)
                .offset(offset)
                .options(
                    load_only(
                        SavedRecipe.id,
                        SavedRecipe.user_id,
                        SavedRecipe.name,
                        SavedRecipe.description,
                        SavedRecipe.prep_time,
                        SavedRecipe.difficulty,
                        SavedRecipe.servings,
                        SavedRecipe.ingredients_needed,
                        SavedRecipe.instructions,
                        SavedRecipe.tags,
                        SavedRecipe.nutrition_notes,
                        SavedRecipe.pantry_usage_score,
                        SavedRecipe.ai_generated,
                        SavedRecipe.ai_provider,
                        SavedRecipe.source,
                        SavedRecipe.times_cooked,
                        SavedRecipe.last_cooked,
                        SavedRecipe.created_at,
                        SavedRecipe.updated_at,
                    )
                )
            )

            # dynamic filters -------------------------------------------------
            if search:
                ilike_term = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        SavedRecipe.name.ilike(ilike_term),
                        SavedRecipe.description.ilike(ilike_term),
                        SavedRecipe.tags.ilike(ilike_term),
                    )
                )
            if difficulty:
                stmt = stmt.where(SavedRecipe.difficulty == difficulty)
            if tags:
                stmt = stmt.where(SavedRecipe.tags.ilike(f"%{tags}%"))

            rows = session.execute(stmt).all()

        # row → pydantic ------------------------------------------------------
        def _loads(text_: Union[str, None]):
            if not text_:
                return []
            try:
                return json.loads(text_)
            except Exception:  # noqa: BLE001
                return []

        responses: List[SavedRecipeResponse] = []
        for saved_rec, avg_rating in rows:
            responses.append(
                SavedRecipeResponse(
                    id=str(saved_rec.id),
                    user_id=str(saved_rec.user_id),
                    name=saved_rec.name,
                    description=saved_rec.description or "",
                    prep_time=saved_rec.prep_time,
                    difficulty=saved_rec.difficulty,
                    servings=saved_rec.servings,
                    ingredients_needed=_loads(saved_rec.ingredients_needed),
                    instructions=_loads(saved_rec.instructions),
                    tags=_loads(saved_rec.tags),
                    nutrition_notes=saved_rec.nutrition_notes or "",
                    pantry_usage_score=saved_rec.pantry_usage_score or 0,
                    ai_generated=bool(saved_rec.ai_generated),
                    ai_provider=saved_rec.ai_provider,
                    source=saved_rec.source or "manual",
                    times_cooked=saved_rec.times_cooked or 0,
                    last_cooked=saved_rec.last_cooked.isoformat() if saved_rec.last_cooked else None,
                    rating=round(avg_rating, 1) if avg_rating is not None else None,
                    created_at=saved_rec.created_at.isoformat() if saved_rec.created_at else None,
                    updated_at=saved_rec.updated_at.isoformat() if saved_rec.updated_at else None,
                )
            )
        return responses

    return await run_in_threadpool(_query)



# ---------------------------------------------------------------------------
# CREATE -- save new recipe
# ---------------------------------------------------------------------------

@router.post("", response_model=SavedRecipeResponse)
async def save_recipe(recipe_data: SavedRecipeCreate, authorization: str = Header(None)):
    """Save a new recipe"""
    logger.info(f"🍽️ Recipe save request: {recipe_data.name}")
    
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user_uuid = uuid.UUID(current_user['sub'])
        
        def _save_recipe():
            from ..models.recipe import SavedRecipe
            with get_db_session() as session:
                # Validate required fields
                if not recipe_data.name or not recipe_data.description:
                    raise HTTPException(status_code=400, detail="Recipe name and description are required")
                
                if recipe_data.prep_time <= 0 or recipe_data.servings <= 0:
                    raise HTTPException(status_code=400, detail="Prep time and servings must be positive numbers")
                
                # Create new saved recipe
                new_recipe = SavedRecipe(
                    user_id=user_uuid,
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
                session.flush()  # Get the ID assigned
                
                logger.info(f"✅ Recipe saved successfully: {new_recipe.id}")
                
                return SavedRecipeResponse(
                    id=str(new_recipe.id),
                    user_id=str(new_recipe.user_id),
                    name=new_recipe.name,
                    description=new_recipe.description or "",
                    prep_time=new_recipe.prep_time,
                    difficulty=new_recipe.difficulty,
                    servings=new_recipe.servings,
                    ingredients_needed=json.loads(new_recipe.ingredients_needed) if new_recipe.ingredients_needed else [],
                    instructions=json.loads(new_recipe.instructions) if new_recipe.instructions else [],
                    tags=json.loads(new_recipe.tags) if new_recipe.tags else [],
                    nutrition_notes=new_recipe.nutrition_notes or "",
                    pantry_usage_score=new_recipe.pantry_usage_score or 0,
                    ai_generated=bool(new_recipe.ai_generated),
                    ai_provider=new_recipe.ai_provider,
                    source=new_recipe.source or "manual",
                    times_cooked=new_recipe.times_cooked or 0,
                    last_cooked=new_recipe.last_cooked.isoformat() if new_recipe.last_cooked else None,
                    rating=None,
                    created_at=new_recipe.created_at.isoformat() if new_recipe.created_at else None,
                    updated_at=new_recipe.updated_at.isoformat() if new_recipe.updated_at else None
                )
        
        return await run_in_threadpool(_save_recipe)
        
    except Exception as e:
        logger.error(f"❌ Error saving recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving recipe: {str(e)}")


# ---------------------------------------------------------------------------
# READ -- get single recipe by ID
# ---------------------------------------------------------------------------

@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_recipe(recipe_id: str, authorization: str = Header(None)):
    """Get a single recipe by ID"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user_uuid = uuid.UUID(current_user['sub'])
        recipe_uuid = uuid.UUID(recipe_id)
        
        def _get_recipe():
            from ..models.recipe import SavedRecipe, RecipeRating
            with get_db_session() as session:
                recipe = session.query(SavedRecipe).filter(
                    SavedRecipe.id == recipe_uuid,
                    SavedRecipe.user_id == user_uuid
                ).first()
                
                if not recipe:
                    raise HTTPException(status_code=404, detail="Recipe not found")
                
                # Get average rating
                avg_rating = session.query(func.avg(RecipeRating.rating)).filter(
                    RecipeRating.recipe_id == recipe_uuid
                ).scalar()
                
                return SavedRecipeResponse(
                    id=str(recipe.id),
                    user_id=str(recipe.user_id),
                    name=recipe.name,
                    description=recipe.description or "",
                    prep_time=recipe.prep_time,
                    difficulty=recipe.difficulty,
                    servings=recipe.servings,
                    ingredients_needed=json.loads(recipe.ingredients_needed) if recipe.ingredients_needed else [],
                    instructions=json.loads(recipe.instructions) if recipe.instructions else [],
                    tags=json.loads(recipe.tags) if recipe.tags else [],
                    nutrition_notes=recipe.nutrition_notes or "",
                    pantry_usage_score=recipe.pantry_usage_score or 0,
                    ai_generated=bool(recipe.ai_generated),
                    ai_provider=recipe.ai_provider,
                    source=recipe.source or "manual",
                    times_cooked=recipe.times_cooked or 0,
                    last_cooked=recipe.last_cooked.isoformat() if recipe.last_cooked else None,
                    rating=round(avg_rating, 1) if avg_rating else None,
                    created_at=recipe.created_at.isoformat() if recipe.created_at else None,
                    updated_at=recipe.updated_at.isoformat() if recipe.updated_at else None
                )
        
        return await run_in_threadpool(_get_recipe)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recipe: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE -- delete recipe
# ---------------------------------------------------------------------------

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, authorization: str = Header(None)):
    """Delete a recipe"""
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user_uuid = uuid.UUID(current_user['sub'])
        recipe_uuid = uuid.UUID(recipe_id)
        
        def _delete_recipe():
            from ..models.recipe import SavedRecipe
            with get_db_session() as session:
                recipe = session.query(SavedRecipe).filter(
                    SavedRecipe.id == recipe_uuid,
                    SavedRecipe.user_id == user_uuid
                ).first()
                
                if not recipe:
                    raise HTTPException(status_code=404, detail="Recipe not found")
                
                session.delete(recipe)
                logger.info(f"✅ Recipe deleted: {recipe_uuid}")
                return {"message": "Recipe deleted successfully"}
        
        return await run_in_threadpool(_delete_recipe)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting recipe: {str(e)}")
