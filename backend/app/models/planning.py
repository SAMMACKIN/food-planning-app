from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="meal_plans")
    planned_meals = relationship("PlannedMeal", back_populates="plan", cascade="all, delete-orphan")


class PlannedMeal(Base):
    __tablename__ = "planned_meals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("meal_plans.id"), nullable=False)
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String, nullable=False)  # breakfast, lunch, dinner, snack
    attendee_count = Column(Integer, nullable=False, default=1)

    plan = relationship("MealPlan", back_populates="planned_meals")
    meal = relationship("Meal", back_populates="planned_meals")
    attendance = relationship("MealAttendance", back_populates="planned_meal", cascade="all, delete-orphan")


class MealAttendance(Base):
    __tablename__ = "meal_attendance"

    planned_meal_id = Column(UUID(as_uuid=True), ForeignKey("planned_meals.id"), primary_key=True)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey("family_members.id"), primary_key=True)

    planned_meal = relationship("PlannedMeal", back_populates="attendance")
    family_member = relationship("FamilyMember", back_populates="meal_attendance")