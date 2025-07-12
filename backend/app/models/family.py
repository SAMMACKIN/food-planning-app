from sqlalchemy import Column, String, DateTime, JSON, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="family_members")
    meal_attendance = relationship("MealAttendance", back_populates="family_member", cascade="all, delete-orphan")


class DietaryRestriction(Base):
    __tablename__ = "dietary_restrictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    type = Column(String, nullable=False)  # allergy, intolerance, preference, medical