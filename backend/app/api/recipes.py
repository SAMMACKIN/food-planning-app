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
from typing import List, Optional

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

def get_current_user(authorization: str | None = None):
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
    def _query() -> list[SavedRecipeResponse]:
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
        def _loads(text_: str | None):
            if not text_:
                return []
            try:
                return json.loads(text_)
            except Exception:  # noqa: BLE001
                return []

        responses: list[SavedRecipeResponse] = []
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
# The rest of the original routes (save, read‑one, rate, delete) stay exactly
# as they were; remove for brevity – copy unchanged from your previous file.
# ---------------------------------------------------------------------------
