from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    timezone = Column(String, default="UTC")
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Added missing field from SQLite schema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    family_members = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    pantry_items = relationship("PantryItem", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    meal_ratings = relationship("MealRating", back_populates="user", cascade="all, delete-orphan")
    user_preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    recommendation_history = relationship("RecommendationHistory", back_populates="user", cascade="all, delete-orphan")
    recipes_v2 = relationship("RecipeV2", back_populates="user", cascade="all, delete-orphan")
    
    # New content type relationships
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    tv_shows = relationship("TVShow", back_populates="user", cascade="all, delete-orphan")
    movies = relationship("Movie", back_populates="user", cascade="all, delete-orphan")