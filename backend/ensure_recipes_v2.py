#!/usr/bin/env python3
"""
Ensure RecipeV2 table exists with correct schema
This runs during app startup to fix schema issues
"""
import logging
import os
from sqlalchemy import create_engine, text, inspect

logger = logging.getLogger(__name__)


def ensure_recipes_v2_table():
    """Ensure RecipeV2 table exists with correct schema"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.warning("No DATABASE_URL found, skipping RecipeV2 table check")
        return
    
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Check if recipes_v2 table exists
        if 'recipes_v2' not in inspector.get_table_names():
            logger.info("Creating recipes_v2 table...")
            
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE recipes_v2 (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id),
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        prep_time INTEGER NOT NULL,
                        difficulty VARCHAR(50) NOT NULL,
                        servings INTEGER NOT NULL,
                        ingredients_needed JSON DEFAULT '[]',
                        instructions JSON DEFAULT '[]',
                        tags JSON DEFAULT '[]',
                        nutrition_notes TEXT DEFAULT '',
                        pantry_usage_score INTEGER DEFAULT 0,
                        source VARCHAR(100) DEFAULT 'user_created',
                        ai_generated BOOLEAN DEFAULT FALSE,
                        ai_provider VARCHAR(50),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                conn.commit()
                logger.info("✅ RecipeV2 table created successfully")
        else:
            # Check if it has the required columns
            columns = [col['name'] for col in inspector.get_columns('recipes_v2')]
            
            if 'ingredients_needed' not in columns:
                logger.info("Adding missing columns to recipes_v2 table...")
                
                with engine.connect() as conn:
                    # Add missing columns one by one
                    if 'ingredients_needed' not in columns:
                        conn.execute(text("ALTER TABLE recipes_v2 ADD COLUMN ingredients_needed JSON DEFAULT '[]';"))
                    if 'pantry_usage_score' not in columns:
                        conn.execute(text("ALTER TABLE recipes_v2 ADD COLUMN pantry_usage_score INTEGER DEFAULT 0;"))
                    if 'ai_provider' not in columns:
                        conn.execute(text("ALTER TABLE recipes_v2 ADD COLUMN ai_provider VARCHAR(50);"))
                    
                    conn.commit()
                    logger.info("✅ RecipeV2 table updated successfully")
            else:
                logger.info("✅ RecipeV2 table schema is up to date")
                
    except Exception as e:
        logger.error(f"❌ Error ensuring RecipeV2 table: {e}")
        # Don't raise - app should continue even if this fails