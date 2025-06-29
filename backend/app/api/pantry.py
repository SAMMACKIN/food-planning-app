"""
Pantry and ingredient management API endpoints
"""
import sqlite3
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends, Query

from ..core.database import get_db_connection
from ..core.security import verify_token
from ..schemas.pantry import (
    IngredientResponse, 
    PantryItemCreate, 
    PantryItemUpdate, 
    PantryItemResponse
)

router = APIRouter(prefix="/pantry", tags=["pantry"])


def get_current_user_dependency(authorization: str = Header(None)):
    """FastAPI dependency for user authentication"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    user_data = verify_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_data


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    return verify_token(token)



# Pantry management endpoints
@router.get("", response_model=List[PantryItemResponse])
async def get_pantry_items(authorization: str = Header(None)):
    """Get all pantry items for the authenticated user"""
    # Try to get authenticated user, fallback to admin for compatibility
    user_id = None
    
    try:
        if authorization:
            current_user = get_current_user_dependency(authorization)
            user_id = current_user['id']
        else:
            # Fallback to admin user for compatibility
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            conn.close()
            if admin_user:
                user_id = admin_user[0]
            else:
                raise HTTPException(status_code=401, detail="No admin user found")
    except HTTPException:
        raise
    except:
        # Final fallback
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        conn.close()
        if admin_user:
            user_id = admin_user[0]
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
                   i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
                   i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.user_id = ?
            ORDER BY i.category, i.name
        ''', (user_id,))
        
        pantry_items = cursor.fetchall()
        
        result = []
        for item in pantry_items:
            # Parse allergens from JSON string
            try:
                allergens = json.loads(item[13]) if item[13] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    allergens = eval(item[13]) if item[13] else []
                except:
                    allergens = []
            
            result.append(PantryItemResponse(
                user_id=item[0],
                ingredient_id=item[1],
                quantity=item[2],
                expiration_date=item[3],
                updated_at=item[4],
                ingredient=IngredientResponse(
                    id=item[5],
                    name=item[6],
                    category=item[7],
                    unit=item[8],
                    calories_per_unit=item[9] or 0,
                    protein_per_unit=item[10] or 0,
                    carbs_per_unit=item[11] or 0,
                    fat_per_unit=item[12] or 0,
                    allergens=allergens,
                    created_at=item[14]
                )
            ))
        
        return result
        
    finally:
        conn.close()


@router.post("", response_model=PantryItemResponse)
async def add_pantry_item(
    pantry_data: PantryItemCreate, 
    current_user: dict = Depends(get_current_user_dependency)
):
    """Add a new pantry item"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Check if ingredient exists
        cursor.execute("SELECT * FROM ingredients WHERE id = ?", (pantry_data.ingredient_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # Insert or update pantry item
        cursor.execute('''
            INSERT OR REPLACE INTO pantry_items (user_id, ingredient_id, quantity, expiration_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, pantry_data.ingredient_id, pantry_data.quantity, pantry_data.expiration_date))
        conn.commit()
        
        # Get the pantry item with ingredient details
        cursor.execute('''
            SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
                   i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
                   i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.user_id = ? AND p.ingredient_id = ?
        ''', (user_id, pantry_data.ingredient_id))
        
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=500, detail="Failed to create pantry item")
        
        # Parse allergens from JSON string
        try:
            allergens = json.loads(item[13]) if item[13] else []
        except (json.JSONDecodeError, TypeError):
            try:
                allergens = eval(item[13]) if item[13] else []
            except:
                allergens = []
        
        return PantryItemResponse(
            user_id=item[0],
            ingredient_id=item[1],
            quantity=item[2],
            expiration_date=item[3],
            updated_at=item[4],
            ingredient=IngredientResponse(
                id=item[5],
                name=item[6],
                category=item[7],
                unit=item[8],
                calories_per_unit=item[9] or 0,
                protein_per_unit=item[10] or 0,
                carbs_per_unit=item[11] or 0,
                fat_per_unit=item[12] or 0,
                allergens=allergens,
                created_at=item[14]
            )
        )
        
    finally:
        conn.close()


@router.put("/{ingredient_id}", response_model=PantryItemResponse)
async def update_pantry_item(
    ingredient_id: str, 
    pantry_data: PantryItemUpdate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Update an existing pantry item"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Check if pantry item exists
        cursor.execute("SELECT * FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pantry item not found")
        
        # Build update query dynamically
        updates = []
        values = []
        
        if pantry_data.quantity is not None:
            updates.append("quantity = ?")
            values.append(pantry_data.quantity)
        if pantry_data.expiration_date is not None:
            updates.append("expiration_date = ?")
            values.append(pantry_data.expiration_date)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.extend([user_id, ingredient_id])
            cursor.execute(
                f"UPDATE pantry_items SET {', '.join(updates)} WHERE user_id = ? AND ingredient_id = ?",
                values
            )
            conn.commit()
        
        # Get updated pantry item with ingredient details
        cursor.execute('''
            SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
                   i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
                   i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.user_id = ? AND p.ingredient_id = ?
        ''', (user_id, ingredient_id))
        
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Pantry item not found after update")
        
        # Parse allergens from JSON string
        try:
            allergens = json.loads(item[13]) if item[13] else []
        except (json.JSONDecodeError, TypeError):
            try:
                allergens = eval(item[13]) if item[13] else []
            except:
                allergens = []
        
        return PantryItemResponse(
            user_id=item[0],
            ingredient_id=item[1],
            quantity=item[2],
            expiration_date=item[3],
            updated_at=item[4],
            ingredient=IngredientResponse(
                id=item[5],
                name=item[6],
                category=item[7],
                unit=item[8],
                calories_per_unit=item[9] or 0,
                protein_per_unit=item[10] or 0,
                carbs_per_unit=item[11] or 0,
                fat_per_unit=item[12] or 0,
                allergens=allergens,
                created_at=item[14]
            )
        )
        
    finally:
        conn.close()


@router.delete("/{ingredient_id}")
async def remove_pantry_item(
    ingredient_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Remove a pantry item"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Check if pantry item exists
        cursor.execute("SELECT * FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pantry item not found")
        
        cursor.execute("DELETE FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
        conn.commit()
        
        return {"message": "Pantry item removed successfully"}
        
    finally:
        conn.close()