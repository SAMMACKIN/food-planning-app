"""
Ingredients API endpoints
"""
import sqlite3
import json
from typing import List
from fastapi import APIRouter, HTTPException, Query

from ..core.database import get_db_connection
from ..schemas.pantry import IngredientResponse

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=List[IngredientResponse])
async def get_ingredients():
    """Get all available ingredients"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, category, unit, calories_per_unit, protein_per_unit, 
                   carbs_per_unit, fat_per_unit, allergens, created_at 
            FROM ingredients 
            ORDER BY category, name
        ''')
        ingredients = cursor.fetchall()
        
        result = []
        for ingredient in ingredients:
            # Parse allergens from JSON string
            try:
                allergens = json.loads(ingredient[8]) if ingredient[8] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    try:
                        allergens = json.loads(ingredient[8]) if ingredient[8] else []
                    except (json.JSONDecodeError, TypeError):
                        allergens = []
                except:
                    allergens = []
            
            result.append(IngredientResponse(
                id=ingredient[0],
                name=ingredient[1],
                category=ingredient[2],
                unit=ingredient[3],
                calories_per_unit=ingredient[4] or 0,
                protein_per_unit=ingredient[5] or 0,
                carbs_per_unit=ingredient[6] or 0,
                fat_per_unit=ingredient[7] or 0,
                allergens=allergens,
                created_at=ingredient[9]
            ))
        
        return result
        
    finally:
        conn.close()


@router.get("/search", response_model=List[IngredientResponse])
async def search_ingredients(q: str = Query(..., description="Search query for ingredient name")):
    """Search ingredients by name"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, category, unit, calories_per_unit, protein_per_unit, 
                   carbs_per_unit, fat_per_unit, allergens, created_at 
            FROM ingredients 
            WHERE name LIKE ? 
            ORDER BY name
            LIMIT 20
        ''', (f'%{q}%',))
        ingredients = cursor.fetchall()
        
        result = []
        for ingredient in ingredients:
            # Parse allergens from JSON string
            try:
                allergens = json.loads(ingredient[8]) if ingredient[8] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    try:
                        allergens = json.loads(ingredient[8]) if ingredient[8] else []
                    except (json.JSONDecodeError, TypeError):
                        allergens = []
                except:
                    allergens = []
            
            result.append(IngredientResponse(
                id=ingredient[0],
                name=ingredient[1],
                category=ingredient[2],
                unit=ingredient[3],
                calories_per_unit=ingredient[4] or 0,
                protein_per_unit=ingredient[5] or 0,
                carbs_per_unit=ingredient[6] or 0,
                fat_per_unit=ingredient[7] or 0,
                allergens=allergens,
                created_at=ingredient[9]
            ))
        
        return result
        
    finally:
        conn.close()