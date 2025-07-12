#!/usr/bin/env python3
"""
Migration script to update RecipeV2 table schema on Railway
"""
import os
import sys
from sqlalchemy import create_engine, text

def migrate_recipes_v2():
    """Update the recipes_v2 table schema"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print(f"🔄 Migrating recipes_v2 table schema...")
    print(f"📊 Database: {database_url.split('@')[-1] if '@' in database_url else 'Unknown'}")
    
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
                    print("📋 Creating new recipes_v2 table...")
                    # Create the table from scratch
                    conn.execute(text("""
                        CREATE TABLE recipes_v2 (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES users(id),
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            prep_time INTEGER NOT NULL,
                            difficulty VARCHAR(50) NOT NULL,
                            servings INTEGER NOT NULL,
                            ingredients_needed JSON NOT NULL DEFAULT '[]',
                            instructions JSON NOT NULL DEFAULT '[]',
                            tags JSON NOT NULL DEFAULT '[]',
                            nutrition_notes TEXT DEFAULT '',
                            pantry_usage_score INTEGER DEFAULT 0,
                            source VARCHAR(100) DEFAULT 'user_created',
                            ai_generated BOOLEAN DEFAULT FALSE,
                            ai_provider VARCHAR(50),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """))
                    print("✅ Created new recipes_v2 table with correct schema")
                else:
                    print("📋 Table exists, checking schema...")
                    
                    # Check if ingredients_needed column exists
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'recipes_v2' 
                            AND column_name = 'ingredients_needed'
                        );
                    """))
                    column_exists = result.scalar()
                    
                    if not column_exists:
                        print("🔄 Adding missing columns to existing table...")
                        
                        # Drop the old table and recreate (safer than ALTER for major schema changes)
                        conn.execute(text("DROP TABLE IF EXISTS recipes_v2 CASCADE;"))
                        
                        # Create the new table
                        conn.execute(text("""
                            CREATE TABLE recipes_v2 (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                user_id UUID NOT NULL REFERENCES users(id),
                                name VARCHAR(255) NOT NULL,
                                description TEXT,
                                prep_time INTEGER NOT NULL,
                                difficulty VARCHAR(50) NOT NULL,
                                servings INTEGER NOT NULL,
                                ingredients_needed JSON NOT NULL DEFAULT '[]',
                                instructions JSON NOT NULL DEFAULT '[]',
                                tags JSON NOT NULL DEFAULT '[]',
                                nutrition_notes TEXT DEFAULT '',
                                pantry_usage_score INTEGER DEFAULT 0,
                                source VARCHAR(100) DEFAULT 'user_created',
                                ai_generated BOOLEAN DEFAULT FALSE,
                                ai_provider VARCHAR(50),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                        """))
                        print("✅ Recreated recipes_v2 table with new schema")
                    else:
                        print("✅ Schema is already up to date")
                
                # Commit the transaction
                trans.commit()
                print("🎉 Migration completed successfully!")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_recipes_v2()
    sys.exit(0 if success else 1)