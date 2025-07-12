"""
Recipe-related SQLAlchemy models
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.database import Base


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