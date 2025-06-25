#!/usr/bin/env python3
"""
Database migration script to add missing columns to meal_plans table
Run this when deploying to environments that don't have the new schema
"""
import sqlite3
import os
import sys

def get_db_path():
    """Get the appropriate database path based on environment"""
    environment = os.getenv('ENVIRONMENT', 'development')
    deployment_id = os.getenv('RAILWAY_DEPLOYMENT_ID')
    
    if environment == 'production' or deployment_id:
        return 'production_food_app.db'
    elif environment == 'preview':
        return 'preview_food_app.db'
    else:
        return 'development_food_app.db'

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def migrate_meal_plans_table():
    """Add missing columns to meal_plans table if they don't exist"""
    db_path = get_db_path()
    print(f"🗄️ Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check and add meal_name column
        if not check_column_exists(cursor, 'meal_plans', 'meal_name'):
            print("➕ Adding meal_name column...")
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN meal_name TEXT")
        else:
            print("✅ meal_name column already exists")
            
        # Check and add meal_description column  
        if not check_column_exists(cursor, 'meal_plans', 'meal_description'):
            print("➕ Adding meal_description column...")
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN meal_description TEXT")
        else:
            print("✅ meal_description column already exists")
            
        # Check and add ai_generated column
        if not check_column_exists(cursor, 'meal_plans', 'ai_generated'):
            print("➕ Adding ai_generated column...")
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE")
        else:
            print("✅ ai_generated column already exists")
            
        # Check and add ai_provider column
        if not check_column_exists(cursor, 'meal_plans', 'ai_provider'):
            print("➕ Adding ai_provider column...")
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN ai_provider TEXT")
        else:
            print("✅ ai_provider column already exists")
        
        # Migrate existing data from recipe_name to meal_name if needed
        cursor.execute("SELECT COUNT(*) FROM meal_plans WHERE meal_name IS NULL AND recipe_name IS NOT NULL")
        needs_migration = cursor.fetchone()[0]
        
        if needs_migration > 0:
            print(f"📝 Migrating {needs_migration} existing records from recipe_name to meal_name...")
            cursor.execute("UPDATE meal_plans SET meal_name = recipe_name WHERE meal_name IS NULL")
        else:
            print("✅ No data migration needed")
        
        conn.commit()
        print("✅ Migration completed successfully")
        
        # Show final schema
        cursor.execute("PRAGMA table_info(meal_plans)")
        columns = cursor.fetchall()
        print("\n📋 Final meal_plans table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Starting meal_plans table migration...")
    success = migrate_meal_plans_table()
    sys.exit(0 if success else 1)