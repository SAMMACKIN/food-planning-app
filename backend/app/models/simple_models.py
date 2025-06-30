"""
Simplified SQLAlchemy models that match the current SQLite schema exactly
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    hashed_password = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    family_members = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    pantry_items = relationship("PantryItem", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    saved_recipes = relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")
    recipe_ratings = relationship("RecipeRating", back_populates="user", cascade="all, delete-orphan")
    meal_reviews = relationship("MealReview", back_populates="user", cascade="all, delete-orphan")


class FamilyMember(Base):
    __tablename__ = "family_members"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer)
    dietary_restrictions = Column(Text)  # JSON string
    preferences = Column(Text)  # JSON string
    created_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="family_members")


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    calories_per_unit = Column(Float, default=0.0)
    protein_per_unit = Column(Float, default=0.0)
    carbs_per_unit = Column(Float, default=0.0)
    fat_per_unit = Column(Float, default=0.0)
    allergens = Column(Text, default="[]")  # JSON string
    created_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    pantry_items = relationship("PantryItem", back_populates="ingredient", cascade="all, delete-orphan")


class PantryItem(Base):
    __tablename__ = "pantry_items"
    __table_args__ = {'extend_existing': True}

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), primary_key=True)
    quantity = Column(Float, nullable=False)
    expiration_date = Column(Date)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="pantry_items")
    ingredient = relationship("Ingredient", back_populates="pantry_items")


class MealPlan(Base):
    __tablename__ = "meal_plans"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String, nullable=False)
    meal_name = Column(String)
    meal_description = Column(Text)
    recipe_data = Column(Text)  # JSON string
    ai_generated = Column(Boolean, default=False)
    ai_provider = Column(String)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="meal_plans")
    meal_reviews = relationship("MealReview", back_populates="meal_plan", cascade="all, delete-orphan")


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    prep_time = Column(Integer, nullable=False)
    difficulty = Column(String, nullable=False)
    servings = Column(Integer, nullable=False)
    ingredients_needed = Column(Text)  # JSON string
    instructions = Column(Text)  # JSON string
    tags = Column(Text)  # JSON string
    nutrition_notes = Column(Text)
    pantry_usage_score = Column(Integer, default=0)
    ai_generated = Column(Boolean, default=False)
    ai_provider = Column(String)
    source = Column(String, default="recommendation")
    times_cooked = Column(Integer, default=0)
    last_cooked = Column(DateTime)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="saved_recipes")
    recipe_ratings = relationship("RecipeRating", back_populates="recipe", cascade="all, delete-orphan")


class RecipeRating(Base):
    __tablename__ = "recipe_ratings"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recipe_id = Column(String, ForeignKey("saved_recipes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    review_text = Column(Text)
    would_make_again = Column(Boolean, default=True)
    cooking_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    recipe = relationship("SavedRecipe", back_populates="recipe_ratings")
    user = relationship("User", back_populates="recipe_ratings")


class MealReview(Base):
    __tablename__ = "meal_reviews"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meal_plan_id = Column(String, ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    review_text = Column(Text)
    would_make_again = Column(Boolean, default=True)
    preparation_notes = Column(Text)
    reviewed_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meal_reviews")
    user = relationship("User", back_populates="meal_reviews")