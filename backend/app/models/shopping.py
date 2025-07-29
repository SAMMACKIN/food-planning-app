"""
Shopping List models
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.database import Base


class ShoppingList(Base):
    """Shopping list model"""
    __tablename__ = 'shopping_lists'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    week_start = Column(DateTime, nullable=True)  # Link to meal plan week
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    shared_with = Column(JSON, default=list)  # List of email addresses
    
    # Status tracking
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    estimated_total_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")


class ShoppingListItem(Base):
    """Shopping list item model"""
    __tablename__ = 'shopping_list_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopping_list_id = Column(UUID(as_uuid=True), ForeignKey('shopping_lists.id'), nullable=False)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.id'), nullable=True)
    
    # Item details
    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    category = Column(String(100), nullable=False)  # Produce, Dairy, Meat, etc.
    priority = Column(String(20), default='normal')  # high, normal, low
    
    # Status and metadata
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    
    # Source tracking
    source_recipes = Column(JSON, default=list)  # List of recipe IDs/names that need this item
    source_meal_plans = Column(JSON, default=list)  # List of meal plan IDs
    manually_added = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    ingredient = relationship("Ingredient")


class ShoppingListTemplate(Base):
    """Template for recurring shopping list items"""
    __tablename__ = 'shopping_list_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template items as JSON
    template_items = Column(JSON, default=list)  # [{"name": "Milk", "quantity": 1, "unit": "gallon", "category": "Dairy"}]
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")