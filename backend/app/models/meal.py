from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

meal_category_mapping = Table(
    'meal_category_mapping',
    Base.metadata,
    Column('meal_id', String, ForeignKey('meals.id')),
    Column('category_id', String, ForeignKey('meal_categories.id'))
)


class Meal(Base):
    __tablename__ = "meals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    prep_time = Column(Integer, nullable=False)  # minutes
    cook_time = Column(Integer, nullable=False)  # minutes
    difficulty = Column(Integer, nullable=False)  # 1-5 scale
    servings = Column(Integer, nullable=False, default=4)
    instructions = Column(JSON, default=[])  # list of instruction steps
    image_url = Column(String)
    nutritional_info = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ingredients = relationship("MealIngredient", back_populates="meal", cascade="all, delete-orphan")
    categories = relationship("MealCategory", secondary=meal_category_mapping, back_populates="meals")
    planned_meals = relationship("PlannedMeal", back_populates="meal", cascade="all, delete-orphan")
    meal_ratings = relationship("MealRating", back_populates="meal", cascade="all, delete-orphan")
    recommendation_history = relationship("RecommendationHistory", back_populates="meal", cascade="all, delete-orphan")


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    meal_id = Column(String, ForeignKey("meals.id"), primary_key=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), primary_key=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    optional = Column(Boolean, default=False)

    meal = relationship("Meal", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="meal_ingredients")


class MealCategory(Base):
    __tablename__ = "meal_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)  # diet, cuisine, meal_type, health, difficulty

    meals = relationship("Meal", secondary=meal_category_mapping, back_populates="categories")