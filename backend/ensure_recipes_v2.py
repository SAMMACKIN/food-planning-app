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
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if recipes_v2 table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'recipes_v2'
                    );
                """))
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.info("Creating recipes_v2 table...")
                    
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
                    logger.info("✅ RecipeV2 table created successfully")
                else:
                    # Check if table has new schema by looking for ingredients_needed column
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'recipes_v2' 
                            AND column_name = 'ingredients_needed'
                        );
                    """))
                    has_new_schema = result.scalar()
                    
                    # Also check if old ingredients column exists (conflict)
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'recipes_v2' 
                            AND column_name = 'ingredients'
                        );
                    """))
                    has_old_schema = result.scalar()
                    
                    if not has_new_schema or has_old_schema:
                        logger.info("Schema conflict detected - recreating recipes_v2 table...")
                        
                        # Drop existing table and recreate with correct schema
                        conn.execute(text("DROP TABLE IF EXISTS recipes_v2 CASCADE;"))
                        
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
                        logger.info("✅ RecipeV2 table recreated with correct schema")
                    else:
                        logger.info("✅ RecipeV2 table schema is up to date")
                
                # Commit the transaction
                trans.commit()
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"❌ Error in RecipeV2 table transaction: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Error ensuring RecipeV2 table: {e}")
        # Don't raise - app should continue even if this fails