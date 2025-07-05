from sqlalchemy import Column, String, DateTime, JSON, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer)
    dietary_restrictions = Column(Text)  # JSON string to match AI expectations
    preferences = Column(Text)  # JSON string to match AI expectations
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="family_members")
    meal_attendance = relationship("MealAttendance", back_populates="family_member", cascade="all, delete-orphan")


class DietaryRestriction(Base):
    __tablename__ = "dietary_restrictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    type = Column(String, nullable=False)  # allergy, intolerance, preference, medical