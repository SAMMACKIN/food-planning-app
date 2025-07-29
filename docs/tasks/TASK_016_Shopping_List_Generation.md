# TASK_016: Shopping List Generation

## Status: PENDING

## Overview
Implement automatic shopping list generation from meal plans with smart quantity calculation, categorization, and sharing capabilities.

## Objectives
1. Auto-generate shopping lists from weekly meal plans
2. Calculate quantities based on servings and attendance
3. Categorize items by store sections
4. Subtract pantry inventory from shopping needs
5. Enable list sharing and export

## Implementation Steps

### 1. Backend Models
```python
# backend/app/models/shopping.py
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class ShoppingList(Base):
    __tablename__ = 'shopping_lists'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    week_start = Column(DateTime, nullable=True)  # Link to meal plan week
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    shared_with = Column(JSON, default=list)  # List of email addresses
    
    # Relationships
    user = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

class ShoppingListItem(Base):
    __tablename__ = 'shopping_list_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopping_list_id = Column(UUID(as_uuid=True), ForeignKey('shopping_lists.id'), nullable=False)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.id'), nullable=True)
    
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    category = Column(String, nullable=False)  # Produce, Dairy, Meat, etc.
    is_checked = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    
    # For meal plan connection
    source_recipes = Column(JSON, default=list)  # List of recipe names
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    ingredient = relationship("Ingredient")
```

### 2. Shopping List Service
```python
# backend/app/services/shopping_list_service.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import defaultdict

class ShoppingListService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_from_meal_plan(
        self, 
        user_id: str, 
        week_start: datetime,
        name: Optional[str] = None
    ) -> ShoppingList:
        # Get meal plans for the week
        week_end = week_start + timedelta(days=7)
        meal_plans = self.db.query(MealPlan).filter(
            MealPlan.user_id == user_id,
            MealPlan.date >= week_start,
            MealPlan.date < week_end
        ).all()
        
        # Aggregate ingredients needed
        ingredients_needed = defaultdict(lambda: {
            'quantity': 0,
            'unit': '',
            'recipes': [],
            'category': ''
        })
        
        for meal_plan in meal_plans:
            if meal_plan.recipe_id:
                recipe = self.db.query(RecipeV2).filter(
                    RecipeV2.id == meal_plan.recipe_id
                ).first()
                
                if recipe and recipe.ingredients:
                    servings_multiplier = meal_plan.servings / recipe.servings
                    
                    for ingredient in recipe.ingredients:
                        key = self._normalize_ingredient_name(ingredient['name'])
                        ingredients_needed[key]['quantity'] += (
                            ingredient.get('quantity', 0) * servings_multiplier
                        )
                        ingredients_needed[key]['unit'] = ingredient.get('unit', '')
                        ingredients_needed[key]['recipes'].append(recipe.name)
                        ingredients_needed[key]['category'] = self._get_category(
                            ingredient['name']
                        )
        
        # Subtract pantry inventory
        pantry_items = self.db.query(PantryItem).filter(
            PantryItem.user_id == user_id,
            PantryItem.quantity > 0
        ).all()
        
        for item in pantry_items:
            key = self._normalize_ingredient_name(item.ingredient.name)
            if key in ingredients_needed:
                ingredients_needed[key]['quantity'] -= item.quantity
                ingredients_needed[key]['in_pantry'] = item.quantity
        
        # Create shopping list
        shopping_list = ShoppingList(
            user_id=user_id,
            name=name or f"Week of {week_start.strftime('%B %d')}",
            week_start=week_start
        )
        self.db.add(shopping_list)
        
        # Create items (only positive quantities)
        for name, data in ingredients_needed.items():
            if data['quantity'] > 0:
                item = ShoppingListItem(
                    shopping_list_id=shopping_list.id,
                    name=name,
                    quantity=round(data['quantity'], 2),
                    unit=data['unit'],
                    category=data['category'],
                    source_recipes=data['recipes']
                )
                self.db.add(item)
        
        self.db.commit()
        return shopping_list
    
    def _normalize_ingredient_name(self, name: str) -> str:
        # Remove common variations (e.g., "tomatoes" -> "tomato")
        # Handle plurals, case, etc.
        return name.lower().strip()
    
    def _get_category(self, ingredient_name: str) -> str:
        # Map ingredients to store categories
        categories = {
            'produce': ['tomato', 'lettuce', 'onion', 'garlic', ...],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', ...],
            'meat': ['chicken', 'beef', 'pork', 'fish', ...],
            'bakery': ['bread', 'rolls', 'tortilla', ...],
            'pantry': ['rice', 'pasta', 'oil', 'flour', ...],
            'frozen': ['frozen peas', 'ice cream', ...],
            'beverages': ['juice', 'soda', 'coffee', ...]
        }
        
        for category, items in categories.items():
            if any(item in ingredient_name.lower() for item in items):
                return category
        
        return 'other'
```

### 3. API Endpoints
```python
# backend/app/api/shopping.py
from fastapi import APIRouter, Depends, Body, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/shopping", tags=["shopping"])

@router.post("/lists/generate")
async def generate_shopping_list(
    week_start: datetime = Body(...),
    name: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ShoppingListService(db)
    shopping_list = service.generate_from_meal_plan(
        current_user.id, 
        week_start,
        name
    )
    return shopping_list

@router.get("/lists")
async def get_shopping_lists(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ShoppingList).filter(
        ShoppingList.user_id == current_user.id
    )
    if active_only:
        query = query.filter(ShoppingList.is_active == True)
    
    return query.order_by(ShoppingList.created_at.desc()).all()

@router.patch("/items/{item_id}/toggle")
async def toggle_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(ShoppingListItem).join(ShoppingList).filter(
        ShoppingListItem.id == item_id,
        ShoppingList.user_id == current_user.id
    ).first()
    
    if item:
        item.is_checked = not item.is_checked
        db.commit()
    
    return item

@router.post("/lists/{list_id}/share")
async def share_list(
    list_id: str,
    emails: List[str] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shopping_list = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == current_user.id
    ).first()
    
    if shopping_list:
        shopping_list.shared_with = emails
        db.commit()
        # Send email notifications
    
    return shopping_list
```

### 4. Frontend Components
```typescript
// frontend/src/pages/Shopping/ShoppingList.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, Checkbox, IconButton,
  Accordion, AccordionSummary, AccordionDetails,
  Fab, Dialog, Button, Chip, Menu
} from '@mui/material';
import {
  ExpandMore, Add, Share, Print, Download,
  CheckCircle, ShoppingCart
} from '@mui/icons-material';

interface ShoppingListProps {
  weekStart?: Date;
}

export const ShoppingList: React.FC<ShoppingListProps> = ({ weekStart }) => {
  const [lists, setLists] = useState<ShoppingList[]>([]);
  const [activeList, setActiveList] = useState<ShoppingList | null>(null);
  const [groupBy, setGroupBy] = useState<'category' | 'recipe'>('category');
  
  const generateList = async () => {
    const response = await api.post('/shopping/lists/generate', {
      week_start: weekStart || new Date()
    });
    setActiveList(response.data);
    fetchLists();
  };
  
  const toggleItem = async (itemId: string) => {
    await api.patch(`/shopping/items/${itemId}/toggle`);
    // Update local state optimistically
    setActiveList(prev => ({
      ...prev!,
      items: prev!.items.map(item =>
        item.id === itemId ? { ...item, is_checked: !item.is_checked } : item
      )
    }));
  };
  
  const exportList = (format: 'pdf' | 'text' | 'email') => {
    // Implementation for different export formats
  };
  
  const shareList = async (emails: string[]) => {
    await api.post(`/shopping/lists/${activeList?.id}/share`, { emails });
  };
  
  const groupedItems = React.useMemo(() => {
    if (!activeList) return {};
    
    return activeList.items.reduce((acc, item) => {
      const key = groupBy === 'category' ? item.category : item.source_recipes[0];
      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {} as Record<string, ShoppingListItem[]>);
  }, [activeList, groupBy]);
  
  const progress = React.useMemo(() => {
    if (!activeList) return 0;
    const checked = activeList.items.filter(i => i.is_checked).length;
    return (checked / activeList.items.length) * 100;
  }, [activeList]);
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Shopping List</Typography>
        <Box>
          <IconButton onClick={() => setGroupBy(groupBy === 'category' ? 'recipe' : 'category')}>
            <SortIcon />
          </IconButton>
          <IconButton onClick={() => shareList([])}>
            <Share />
          </IconButton>
          <IconButton onClick={() => exportList('pdf')}>
            <Print />
          </IconButton>
        </Box>
      </Box>
      
      {activeList && (
        <>
          <LinearProgress variant="determinate" value={progress} sx={{ mb: 2 }} />
          <Typography variant="body2" sx={{ mb: 3 }}>
            {activeList.items.filter(i => i.is_checked).length} of {activeList.items.length} items
          </Typography>
          
          {Object.entries(groupedItems).map(([group, items]) => (
            <Accordion key={group} defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="h6">{group}</Typography>
                <Chip 
                  label={`${items.filter(i => i.is_checked).length}/${items.length}`}
                  size="small"
                  sx={{ ml: 2 }}
                />
              </AccordionSummary>
              <AccordionDetails>
                {items.map(item => (
                  <Box key={item.id} sx={{ display: 'flex', alignItems: 'center', py: 1 }}>
                    <Checkbox
                      checked={item.is_checked}
                      onChange={() => toggleItem(item.id)}
                    />
                    <Box sx={{ flex: 1 }}>
                      <Typography
                        sx={{
                          textDecoration: item.is_checked ? 'line-through' : 'none',
                          color: item.is_checked ? 'text.secondary' : 'text.primary'
                        }}
                      >
                        {item.quantity} {item.unit} {item.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        For: {item.source_recipes.join(', ')}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </AccordionDetails>
            </Accordion>
          ))}
        </>
      )}
      
      <Fab
        color="primary"
        onClick={generateList}
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
      >
        <Add />
      </Fab>
    </Box>
  );
};
```

### 5. Additional Features
- **Smart Quantity Merging**: Combine same ingredients from different recipes
- **Unit Conversion**: Convert between units (e.g., 3 tsp → 1 tbsp)
- **Store Layout**: Order items by typical store layout
- **Recurring Items**: Add frequently bought items automatically
- **Budget Tracking**: Add price estimates and track spending
- **Barcode Scanning**: Scan items to mark as purchased

## Success Criteria
- Shopping lists generate automatically from meal plans
- Pantry inventory is subtracted from needs
- Items are well-categorized by store section
- Users can check off items while shopping
- Lists can be shared via email/link
- Export options available (PDF, text)
- Mobile-friendly interface

## Dependencies
- Meal planning system
- Pantry inventory
- Recipe ingredients data
- Email service for sharing

## Estimated Time: 4-5 days