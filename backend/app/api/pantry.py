"""
Pantry and ingredient management API endpoints
"""
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends, Query

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..models.ingredient import Ingredient, PantryItem
from ..models.user import User
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
    user_data = AuthService.verify_user_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        'sub': user_data['id'],
        'id': user_data['id'],
        'email': user_data['email'],
        'name': user_data['name'],
        'is_admin': user_data['is_admin']
    }


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    user_data = AuthService.verify_user_token(token)
    if user_data:
        return {
            'sub': user_data['id'],
            'id': user_data['id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'is_admin': user_data['is_admin']
        }
    return None



# Pantry management endpoints
@router.get("", response_model=List[PantryItemResponse])
async def get_pantry_items(current_user: dict = Depends(get_current_user_dependency)):
    """Get all pantry items for the authenticated user"""
    with get_db_session() as session:
        pantry_items = session.query(PantryItem).join(Ingredient).filter(
            PantryItem.user_id == current_user["id"]
        ).all()
        
        result = []
        for item in pantry_items:
            result.append(PantryItemResponse(
                user_id=str(item.user_id),
                ingredient_id=str(item.ingredient_id),
                quantity=item.quantity,
                expiration_date=item.expiration_date.isoformat() if item.expiration_date else None,
                updated_at=item.updated_at.isoformat() if item.updated_at else None,
                ingredient=IngredientResponse(
                    id=str(item.ingredient.id),
                    name=item.ingredient.name,
                    category=item.ingredient.category.name if item.ingredient.category else "Other",
                    unit=item.ingredient.unit,
                    calories_per_unit=item.ingredient.nutritional_info.get("calories", 0) if item.ingredient.nutritional_info else 0,
                    protein_per_unit=item.ingredient.nutritional_info.get("protein", 0) if item.ingredient.nutritional_info else 0,
                    carbs_per_unit=item.ingredient.nutritional_info.get("carbs", 0) if item.ingredient.nutritional_info else 0,
                    fat_per_unit=item.ingredient.nutritional_info.get("fat", 0) if item.ingredient.nutritional_info else 0,
                    allergens=item.ingredient.allergens or [],
                    created_at=None  # Not available in new model
                )
            ))
        
        return result


@router.post("", response_model=PantryItemResponse)
async def add_pantry_item(
    pantry_data: PantryItemCreate, 
    current_user: dict = Depends(get_current_user_dependency)
):
    """Add a new pantry item"""
    with get_db_session() as session:
        # Check if ingredient exists
        ingredient = session.query(Ingredient).filter(
            Ingredient.id == pantry_data.ingredient_id
        ).first()
        
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # Check if pantry item already exists
        existing_item = session.query(PantryItem).filter(
            PantryItem.user_id == current_user["id"],
            PantryItem.ingredient_id == pantry_data.ingredient_id
        ).first()
        
        if existing_item:
            # Update existing item
            existing_item.quantity = pantry_data.quantity
            existing_item.expiration_date = pantry_data.expiration_date
            session.commit()
            session.refresh(existing_item)
            pantry_item = existing_item
        else:
            # Create new pantry item
            pantry_item = PantryItem(
                user_id=current_user["id"],
                ingredient_id=pantry_data.ingredient_id,
                quantity=pantry_data.quantity,
                expiration_date=pantry_data.expiration_date
            )
            session.add(pantry_item)
            session.commit()
            session.refresh(pantry_item)
        
        return PantryItemResponse(
            user_id=str(pantry_item.user_id),
            ingredient_id=str(pantry_item.ingredient_id),
            quantity=pantry_item.quantity,
            expiration_date=pantry_item.expiration_date.isoformat() if pantry_item.expiration_date else None,
            updated_at=pantry_item.updated_at.isoformat() if pantry_item.updated_at else None,
            ingredient=IngredientResponse(
                id=str(ingredient.id),
                name=ingredient.name,
                category=ingredient.category.name if ingredient.category else "Other",
                unit=ingredient.unit,
                calories_per_unit=ingredient.nutritional_info.get("calories", 0) if ingredient.nutritional_info else 0,
                protein_per_unit=ingredient.nutritional_info.get("protein", 0) if ingredient.nutritional_info else 0,
                carbs_per_unit=ingredient.nutritional_info.get("carbs", 0) if ingredient.nutritional_info else 0,
                fat_per_unit=ingredient.nutritional_info.get("fat", 0) if ingredient.nutritional_info else 0,
                allergens=ingredient.allergens or [],
                created_at=None  # Not available in new model
            )
        )


@router.put("/{ingredient_id}", response_model=PantryItemResponse)
async def update_pantry_item(
    ingredient_id: str, 
    pantry_data: PantryItemUpdate,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Update an existing pantry item"""
    with get_db_session() as session:
        # Find the pantry item
        pantry_item = session.query(PantryItem).filter(
            PantryItem.user_id == current_user["id"],
            PantryItem.ingredient_id == ingredient_id
        ).first()
        
        if not pantry_item:
            raise HTTPException(status_code=404, detail="Pantry item not found")
        
        # Update fields that were provided
        if pantry_data.quantity is not None:
            pantry_item.quantity = pantry_data.quantity
        if pantry_data.expiration_date is not None:
            pantry_item.expiration_date = pantry_data.expiration_date
        
        session.commit()
        session.refresh(pantry_item)
        
        # Get ingredient details
        ingredient = session.query(Ingredient).filter(
            Ingredient.id == ingredient_id
        ).first()
        
        return PantryItemResponse(
            user_id=str(pantry_item.user_id),
            ingredient_id=str(pantry_item.ingredient_id),
            quantity=pantry_item.quantity,
            expiration_date=pantry_item.expiration_date.isoformat() if pantry_item.expiration_date else None,
            updated_at=pantry_item.updated_at.isoformat() if pantry_item.updated_at else None,
            ingredient=IngredientResponse(
                id=str(ingredient.id),
                name=ingredient.name,
                category=ingredient.category.name if ingredient.category else "Other",
                unit=ingredient.unit,
                calories_per_unit=ingredient.nutritional_info.get("calories", 0) if ingredient.nutritional_info else 0,
                protein_per_unit=ingredient.nutritional_info.get("protein", 0) if ingredient.nutritional_info else 0,
                carbs_per_unit=ingredient.nutritional_info.get("carbs", 0) if ingredient.nutritional_info else 0,
                fat_per_unit=ingredient.nutritional_info.get("fat", 0) if ingredient.nutritional_info else 0,
                allergens=ingredient.allergens or [],
                created_at=None  # Not available in new model
            )
        )


@router.delete("/{ingredient_id}")
async def remove_pantry_item(
    ingredient_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Remove a pantry item"""
    with get_db_session() as session:
        # Find the pantry item
        pantry_item = session.query(PantryItem).filter(
            PantryItem.user_id == current_user["id"],
            PantryItem.ingredient_id == ingredient_id
        ).first()
        
        if not pantry_item:
            raise HTTPException(status_code=404, detail="Pantry item not found")
        
        session.delete(pantry_item)
        session.commit()
        
        return {"message": "Pantry item removed successfully"}