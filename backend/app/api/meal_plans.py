"""
Meal planning and meal review API endpoints
"""
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..schemas.meals import (
    MealPlanCreate, 
    MealPlanUpdate, 
    MealPlanResponse,
    MealReviewCreate,
    MealReviewUpdate,
    MealReviewResponse
)

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


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
    except Exception:
        return None


@router.get("", response_model=List[MealPlanResponse])
async def get_meal_plans(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    authorization: str = Header(None)
):
    """Get meal plans for current user, optionally filtered by date range"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        user_id = current_user['sub']
        
        # Build query with optional date filtering
        if start_date and end_date:
            result = session.execute(text('''
                SELECT id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider, created_at
                FROM meal_plans 
                WHERE user_id = :user_id AND date BETWEEN :start_date AND :end_date
                ORDER BY date, 
                    CASE meal_type 
                        WHEN 'breakfast' THEN 1 
                        WHEN 'lunch' THEN 2 
                        WHEN 'dinner' THEN 3 
                        WHEN 'snack' THEN 4 
                    END
            '''), {'user_id': user_id, 'start_date': start_date, 'end_date': end_date})
        else:
            result = session.execute(text('''
                SELECT id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider, created_at
                FROM meal_plans 
                WHERE user_id = :user_id
                ORDER BY date DESC, 
                    CASE meal_type 
                        WHEN 'breakfast' THEN 1 
                        WHEN 'lunch' THEN 2 
                        WHEN 'dinner' THEN 3 
                        WHEN 'snack' THEN 4 
                    END
            '''), {'user_id': user_id})
        
        meal_plans = result.fetchall()
        
        result = []
        for plan in meal_plans:
            # Parse recipe_data from JSON/eval
            try:
                recipe_data = json.loads(plan[6]) if plan[6] else None
            except (json.JSONDecodeError, TypeError):
                recipe_data = None
            
            result.append(MealPlanResponse(
                id=str(plan[0]),
                user_id=str(plan[1]),
                date=plan[2],
                meal_type=plan[3],
                meal_name=plan[4] or "",
                meal_description=plan[5],
                recipe_data=recipe_data,
                ai_generated=plan[7] or False,
                ai_provider=plan[8],
                created_at=plan[9].isoformat() if plan[9] else None
            ))
        
        return result


@router.post("", response_model=MealPlanResponse)
async def create_meal_plan(
    meal_plan_data: MealPlanCreate, 
    authorization: str = Header(None)
):
    """Create a new meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    with get_db_session() as session:
        from sqlalchemy import text
        
        user_id = current_user['sub']
        meal_plan_id = str(uuid.uuid4())
        
        # Check if meal already exists for this slot
        result = session.execute(text(
            "SELECT id FROM meal_plans WHERE user_id = :user_id AND date = :date AND meal_type = :meal_type"
        ), {'user_id': user_id, 'date': meal_plan_data.date, 'meal_type': meal_plan_data.meal_type})
        
        if result.fetchone():
            raise HTTPException(status_code=400, detail="Meal already planned for this time slot")
        
        # Insert new meal plan
        recipe_data_str = json.dumps(meal_plan_data.recipe_data) if meal_plan_data.recipe_data else None
        
        session.execute(text('''
            INSERT INTO meal_plans 
            (id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider)
            VALUES (:id, :user_id, :date, :meal_type, :meal_name, :meal_description, :recipe_data, :ai_generated, :ai_provider)
        '''), {
            'id': meal_plan_id,
            'user_id': user_id,
            'date': meal_plan_data.date,
            'meal_type': meal_plan_data.meal_type,
            'meal_name': meal_plan_data.meal_name,
            'meal_description': meal_plan_data.meal_description,
            'recipe_data': recipe_data_str,
            'ai_generated': meal_plan_data.ai_generated,
            'ai_provider': meal_plan_data.ai_provider
        })
        
        # Get the created meal plan
        result = session.execute(text('''
            SELECT id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider, created_at
            FROM meal_plans WHERE id = :meal_plan_id
        '''), {'meal_plan_id': meal_plan_id})
        meal_plan = result.fetchone()
        
        if not meal_plan:
            raise HTTPException(status_code=500, detail="Failed to create meal plan")
        
        # Parse recipe_data from JSON  
        try:
            recipe_data = json.loads(meal_plan[6]) if meal_plan[6] else None
        except (json.JSONDecodeError, TypeError):
            recipe_data = None
        
        return MealPlanResponse(
            id=str(meal_plan[0]),
            user_id=str(meal_plan[1]),
            date=meal_plan[2],
            meal_type=meal_plan[3],
            meal_name=meal_plan[4] or "",
            meal_description=meal_plan[5],
            recipe_data=recipe_data,
            ai_generated=meal_plan[7] or False,
            ai_provider=meal_plan[8],
            created_at=meal_plan[9].isoformat() if meal_plan[9] else None
        )


@router.put("/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    meal_plan_id: str, 
    meal_plan_data: MealPlanUpdate,
    authorization: str = Header(None)
):
    """Update an existing meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if meal plan exists and belongs to user
        cursor.execute("SELECT user_id FROM meal_plans WHERE id = ?", (meal_plan_id,))
        meal_plan = cursor.fetchone()
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        if meal_plan[0] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build update query dynamically
        updates = []
        values = []
        
        if meal_plan_data.meal_name is not None:
            updates.append("meal_name = ?")
            values.append(meal_plan_data.meal_name)
        if meal_plan_data.meal_description is not None:
            updates.append("meal_description = ?")
            values.append(meal_plan_data.meal_description)
        if meal_plan_data.recipe_data is not None:
            updates.append("recipe_data = ?")
            values.append(json.dumps(meal_plan_data.recipe_data))
        
        if updates:
            values.append(meal_plan_id)
            cursor.execute(
                f"UPDATE meal_plans SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
        
        # Get updated meal plan
        cursor.execute('''
            SELECT id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider, created_at
            FROM meal_plans WHERE id = ?
        ''', (meal_plan_id,))
        meal_plan = cursor.fetchone()
        
        # Parse recipe_data from JSON
        try:
            recipe_data = json.loads(meal_plan[6]) if meal_plan[6] else None
        except (json.JSONDecodeError, TypeError):
            recipe_data = None
        
        return MealPlanResponse(
            id=meal_plan[0],
            user_id=meal_plan[1],
            date=meal_plan[2],
            meal_type=meal_plan[3],
            meal_name=meal_plan[4] or "",
            meal_description=meal_plan[5],
            recipe_data=recipe_data,
            ai_generated=meal_plan[7] or False,
            ai_provider=meal_plan[8],
            created_at=meal_plan[9]
        )
        
    finally:
        conn.close()


@router.delete("/{meal_plan_id}")
async def delete_meal_plan(
    meal_plan_id: str,
    authorization: str = Header(None)
):
    """Delete a meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if meal plan exists and belongs to user
        cursor.execute("SELECT user_id FROM meal_plans WHERE id = ?", (meal_plan_id,))
        meal_plan = cursor.fetchone()
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        if meal_plan[0] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete meal plan (reviews will be cascade deleted if table exists)
        cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_plan_id,))
        conn.commit()
        
        return {"message": "Meal plan deleted successfully"}
        
    finally:
        conn.close()


# Meal Review endpoints (if meal_reviews table exists)
@router.get("/{meal_plan_id}/reviews", response_model=List[MealReviewResponse])
async def get_meal_reviews(meal_plan_id: str):
    """Get reviews for a specific meal plan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if meal_reviews table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='meal_reviews'
        """)
        if not cursor.fetchone():
            # Table doesn't exist, return empty list
            return []
        
        cursor.execute('''
            SELECT id, meal_plan_id, user_id, rating, review_text, 
                   would_make_again, preparation_notes, reviewed_at
            FROM meal_reviews 
            WHERE meal_plan_id = ?
            ORDER BY reviewed_at DESC
        ''', (meal_plan_id,))
        
        reviews = cursor.fetchall()
        
        return [
            MealReviewResponse(
                id=review[0],
                meal_plan_id=review[1],
                user_id=review[2],
                rating=review[3],
                review_text=review[4],
                would_make_again=bool(review[5]) if review[5] is not None else True,
                preparation_notes=review[6],
                reviewed_at=review[7]
            )
            for review in reviews
        ]
        
    finally:
        conn.close()


@router.post("/{meal_plan_id}/reviews", response_model=MealReviewResponse)
async def create_meal_review(
    meal_plan_id: str, 
    review_data: MealReviewCreate, 
    authorization: str = Header(None)
):
    """Create a review for a meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['sub']
        
        # Check if meal_reviews table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='meal_reviews'
        """)
        if not cursor.fetchone():
            raise HTTPException(status_code=501, detail="Meal reviews feature not implemented yet")
        
        # Check if meal plan exists
        cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_plan_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        # Check if user already reviewed this meal
        cursor.execute(
            "SELECT id FROM meal_reviews WHERE meal_plan_id = ? AND user_id = ?",
            (meal_plan_id, user_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You have already reviewed this meal")
        
        review_id = str(uuid.uuid4())
        
        # Insert new review
        cursor.execute('''
            INSERT INTO meal_reviews 
            (id, meal_plan_id, user_id, rating, review_text, would_make_again, preparation_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            review_id,
            meal_plan_id,
            user_id,
            review_data.rating,
            review_data.review_text,
            review_data.would_make_again,
            review_data.preparation_notes
        ))
        conn.commit()
        
        # Get the created review
        cursor.execute('''
            SELECT id, meal_plan_id, user_id, rating, review_text, 
                   would_make_again, preparation_notes, reviewed_at
            FROM meal_reviews WHERE id = ?
        ''', (review_id,))
        review = cursor.fetchone()
        
        if not review:
            raise HTTPException(status_code=500, detail="Failed to create review")
        
        return MealReviewResponse(
            id=review[0],
            meal_plan_id=review[1],
            user_id=review[2],
            rating=review[3],
            review_text=review[4],
            would_make_again=bool(review[5]) if review[5] is not None else True,
            preparation_notes=review[6],
            reviewed_at=review[7]
        )
        
    finally:
        conn.close()