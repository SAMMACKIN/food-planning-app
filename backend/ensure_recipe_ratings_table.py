#!/usr/bin/env python3
"""
Ensure recipe_ratings table exists in the database
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

def ensure_recipe_ratings_table():
    """Ensure recipe_ratings table exists"""
    settings = get_settings()
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Check if table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"Existing tables: {existing_tables}")
    
    if 'recipe_ratings' in existing_tables:
        print("✅ recipe_ratings table already exists")
        return
    
    print("🔧 Creating recipe_ratings table...")
    
    # Create the table
    metadata = MetaData()
    
    recipe_ratings = Table(
        'recipe_ratings',
        metadata,
        Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('recipe_id', UUID(as_uuid=True), ForeignKey('recipes_v2.id', ondelete='CASCADE'), nullable=False),
        Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), nullable=False),
        Column('rating', Integer, nullable=False),
        Column('review_text', Text),
        Column('would_make_again', Boolean, default=True),
        Column('cooking_notes', Text),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    
    try:
        metadata.create_all(engine)
        print("✅ recipe_ratings table created successfully")
    except Exception as e:
        print(f"❌ Error creating recipe_ratings table: {e}")
        # If foreign key constraint fails, create without constraints
        try:
            print("🔧 Trying to create table without foreign key constraints...")
            recipe_ratings_no_fk = Table(
                'recipe_ratings',
                metadata,
                Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
                Column('recipe_id', UUID(as_uuid=True), nullable=False),
                Column('user_id', UUID(as_uuid=True), nullable=False),
                Column('rating', Integer, nullable=False),
                Column('review_text', Text),
                Column('would_make_again', Boolean, default=True),
                Column('cooking_notes', Text),
                Column('created_at', DateTime(timezone=True), server_default=func.now()),
                Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
            )
            metadata.drop_all(engine, tables=[recipe_ratings])  # Clean up failed attempt
            metadata = MetaData()  # Reset metadata
            recipe_ratings_no_fk.tometadata(metadata)
            metadata.create_all(engine)
            print("✅ recipe_ratings table created successfully (without foreign key constraints)")
        except Exception as e2:
            print(f"❌ Failed to create table even without constraints: {e2}")
            raise

if __name__ == "__main__":
    ensure_recipe_ratings_table()