from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class MealRating(Base):
    __tablename__ = "meal_ratings"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    meal_id = Column(String, ForeignKey("meals.id"), primary_key=True)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="meal_ratings")
    meal = relationship("Meal", back_populates="meal_ratings")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    preference_type = Column(String, nullable=False)  # cuisine, diet, health_goal, etc.
    value = Column(String, nullable=False)
    weight = Column(Float, default=1.0)  # importance weight for recommendations

    user = relationship("User", back_populates="user_preferences")


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    meal_id = Column(String, ForeignKey("meals.id"), nullable=False)
    recommended_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted = Column(String)  # accepted, rejected, ignored
    feedback = Column(String)

    user = relationship("User", back_populates="recommendation_history")
    meal = relationship("Meal", back_populates="recommendation_history")