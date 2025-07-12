from sqlalchemy import Column, String, DateTime, JSON, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class IngredientCategory(Base):
    __tablename__ = "ingredient_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    parent_category_id = Column(String, ForeignKey("ingredient_categories.id"))

    parent_category = relationship("IngredientCategory", remote_side=[id])
    subcategories = relationship("IngredientCategory", back_populates="parent_category")
    ingredients = relationship("Ingredient", back_populates="category")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    category_id = Column(String, ForeignKey("ingredient_categories.id"))
    unit = Column(String, nullable=False)  # grams, cups, pieces, etc.
    nutritional_info = Column(JSON, default={})
    allergens = Column(JSON, default=[])  # list of allergen names

    category = relationship("IngredientCategory", back_populates="ingredients")
    pantry_items = relationship("PantryItem", back_populates="ingredient")
    meal_ingredients = relationship("MealIngredient", back_populates="ingredient")


class PantryItem(Base):
    __tablename__ = "user_pantry"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), primary_key=True)
    quantity = Column(Float, nullable=False, default=0)
    expiration_date = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="pantry_items")
    ingredient = relationship("Ingredient", back_populates="pantry_items")