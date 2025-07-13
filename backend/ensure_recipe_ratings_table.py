#!/usr/bin/env python3
"""
Ensure recipe_ratings table exists in the database
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

def ensure_recipe_ratings_table():
    """Ensure recipe_ratings table exists with correct schema"""
    settings = get_settings()
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Check if table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"Existing tables: {existing_tables}")
    
    if 'recipe_ratings' in existing_tables:
        print("🔍 recipe_ratings table exists, checking schema...")
        # Check if all required columns exist
        columns = [col['name'] for col in inspector.get_columns('recipe_ratings')]
        print(f"Existing columns: {columns}")
        
        required_columns = ['id', 'recipe_id', 'user_id', 'rating', 'review_text', 'would_make_again', 'cooking_notes', 'created_at', 'updated_at']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            print("🔧 Recreating table with correct schema...")
            # Drop and recreate the table
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE recipe_ratings CASCADE"))
                conn.commit()
        else:
            print("✅ recipe_ratings table has correct schema")
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
            # Drop the existing partial table first
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS recipe_ratings CASCADE"))
                conn.commit()
            
            # Create new metadata and table without foreign keys
            metadata_no_fk = MetaData()
            recipe_ratings_no_fk = Table(
                'recipe_ratings',
                metadata_no_fk,
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
            metadata_no_fk.create_all(engine)
            print("✅ recipe_ratings table created successfully (without foreign key constraints)")
        except Exception as e2:
            print(f"❌ Failed to create table even without constraints: {e2}")
            raise

if __name__ == "__main__":
    ensure_recipe_ratings_table()