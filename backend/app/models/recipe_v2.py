"""
RecipeV2 - Clean, simple recipe model
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.database import Base


class RecipeV2(Base):
    """
    Simple, clean recipe model - no complexity, just what we need
    """
    __tablename__ = "recipes_v2"

    # Basic fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Recipe details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    prep_time = Column(Integer, nullable=False)  # minutes
    difficulty = Column(String(50), nullable=False)  # Easy, Medium, Hard
    servings = Column(Integer, nullable=False)
    
    # JSON fields - simple and direct
    ingredients = Column(JSON, nullable=False, default=list)
    instructions = Column(JSON, nullable=False, default=list)
    tags = Column(JSON, nullable=False, default=list)
    
    # Optional metadata
    nutrition_notes = Column(Text)
    source = Column(String(100), default="manual")  # manual, ai, imported
    ai_generated = Column(String(10), default="false")  # Store as string to avoid bool issues
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Simple relationship
    user = relationship("User", back_populates="recipes_v2")