"""
Shopping List schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ShoppingListItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    quantity: float = Field(..., gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    category: str = Field(..., max_length=100)
    priority: str = Field(default='normal', regex=r'^(high|normal|low)$')
    notes: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)


class ShoppingListItemCreate(ShoppingListItemBase):
    ingredient_id: Optional[str] = None
    source_recipes: List[str] = Field(default_factory=list)
    source_meal_plans: List[str] = Field(default_factory=list)
    manually_added: bool = False


class ShoppingListItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field(None, regex=r'^(high|normal|low)$')
    is_completed: Optional[bool] = None
    notes: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)


class ShoppingListItemResponse(ShoppingListItemBase):
    id: str
    shopping_list_id: str
    ingredient_id: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    source_recipes: List[str]
    source_meal_plans: List[str]
    manually_added: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShoppingListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    is_active: bool = True
    shared_with: List[str] = Field(default_factory=list)


class ShoppingListCreate(ShoppingListBase):
    week_start: Optional[datetime] = None
    items: List[ShoppingListItemCreate] = Field(default_factory=list)


class ShoppingListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    shared_with: Optional[List[str]] = None


class ShoppingListResponse(ShoppingListBase):
    id: str
    user_id: str
    week_start: Optional[datetime] = None
    total_items: int
    completed_items: int
    estimated_total_cost: float
    created_at: datetime
    updated_at: datetime
    items: List[ShoppingListItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ShoppingListSummary(BaseModel):
    id: str
    name: str
    total_items: int
    completed_items: int
    completion_percentage: float
    estimated_total_cost: float
    week_start: Optional[datetime] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class GenerateShoppingListRequest(BaseModel):
    week_start: datetime
    week_end: Optional[datetime] = None
    name: Optional[str] = None
    include_pantry_check: bool = True
    meal_plan_ids: Optional[List[str]] = None  # Specific meal plans, if not provided uses week range


class BulkUpdateItemsRequest(BaseModel):
    item_ids: List[str]
    completed: bool


class ShoppingListTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_items: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class ShoppingListTemplateCreate(ShoppingListTemplateBase):
    pass


class ShoppingListTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_items: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class ShoppingListTemplateResponse(ShoppingListTemplateBase):
    id: str
    user_id: str
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True