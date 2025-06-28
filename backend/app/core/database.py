"""
Database connection and utilities
"""
import sqlite3
import os
import logging
from typing import Optional
from contextlib import contextmanager
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_db_path() -> str:
    """Get the database file path"""
    db_path = settings.DB_PATH
    deployment_id = settings.RAILWAY_DEPLOYMENT_ID
    environment = settings.ENVIRONMENT
    
    logger.info(f"🗄️ Database Configuration:")
    logger.info(f"   Environment: {environment}")
    logger.info(f"   Deployment ID: {deployment_id}")
    logger.info(f"   Database Path: {db_path}")
    logger.info(f"   Full Path: {os.path.join(os.getcwd(), db_path)}")
    
    return db_path


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with improved error handling"""
    db_path = get_db_path()
    
    # Log the actual database being used
    logger.info(f"🔗 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Test the connection
        conn.execute("SELECT 1")
        
        logger.info(f"✅ Database connection successful")
        return conn
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(f"   Database path: {db_path}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        logger.error(f"   Database exists: {os.path.exists(db_path)}")
        raise


@contextmanager
def get_db_cursor():
    """Context manager for database operations with improved transaction handling"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start transaction
        conn.execute("BEGIN")
        
        yield cursor, conn
        
        # Commit transaction
        conn.commit()
        logger.debug("✅ Database transaction committed")
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            logger.error(f"❌ Database transaction rolled back due to SQLite error: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
            logger.error(f"❌ Database transaction rolled back due to error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("🔒 Database connection closed")


def verify_database_schema():
    """Verify that the database has all required tables and columns"""
    logger.info("🔍 Verifying database schema...")
    
    required_tables = {
        'users': ['id', 'email', 'name', 'hashed_password', 'timezone', 'is_active', 'is_admin', 'created_at'],
        'saved_recipes': ['id', 'user_id', 'name', 'description', 'prep_time', 'difficulty', 'servings', 
                         'ingredients_needed', 'instructions', 'tags', 'nutrition_notes', 'pantry_usage_score',
                         'ai_generated', 'ai_provider', 'source', 'times_cooked', 'last_cooked', 'created_at', 'updated_at'],
        'recipe_ratings': ['id', 'recipe_id', 'user_id', 'rating', 'review_text', 'would_make_again', 'cooking_notes', 'created_at'],
        'meal_plans': ['id', 'user_id', 'date', 'meal_type', 'meal_name', 'meal_description', 'recipe_data', 
                      'ai_generated', 'ai_provider', 'created_at']
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        missing_tables = set(required_tables.keys()) - existing_tables
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check if all required columns exist in each table
        for table_name, required_columns in required_tables.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            missing_columns = set(required_columns) - existing_columns
            if missing_columns:
                logger.error(f"❌ Table {table_name} missing columns: {missing_columns}")
                return False
        
        logger.info("✅ Database schema verification passed")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema verification failed: {e}")
        return False


def ensure_separate_databases():
    """Ensure different environments use separate databases"""
    db_path = get_db_path()
    env = settings.ENVIRONMENT
    
    logger.info(f"🔒 Database isolation check:")
    logger.info(f"   Environment: {env}")
    logger.info(f"   Database file: {db_path}")
    
    if env == "production" and "production" not in db_path:
        logger.warning("⚠️ Production environment not using production database!")
    elif env == "preview" and "preview" not in db_path:
        logger.warning("⚠️ Preview environment not using preview database!")
    elif env == "test" and "test" not in db_path:
        logger.warning("⚠️ Test environment not using test database!")
    else:
        logger.info("✅ Database isolation configured correctly")


def init_database():
    """Initialize the database with required tables"""
    logger.info("🗄️  Initializing database...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            hashed_password TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create family_members table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            dietary_restrictions TEXT,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create ingredients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            calories_per_unit REAL DEFAULT 0,
            protein_per_unit REAL DEFAULT 0,
            carbs_per_unit REAL DEFAULT 0,
            fat_per_unit REAL DEFAULT 0,
            allergens TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create pantry_items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pantry_items (
            user_id TEXT NOT NULL,
            ingredient_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            expiration_date DATE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, ingredient_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
        ''')
        
        # Create meal_plans table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            meal_type TEXT NOT NULL,
            meal_name TEXT,
            meal_description TEXT,
            recipe_data TEXT,
            ai_generated BOOLEAN DEFAULT FALSE,
            ai_provider TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create saved_recipes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_recipes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            prep_time INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            servings INTEGER NOT NULL,
            ingredients_needed TEXT,
            instructions TEXT,
            tags TEXT,
            nutrition_notes TEXT,
            pantry_usage_score INTEGER DEFAULT 0,
            ai_generated BOOLEAN DEFAULT FALSE,
            ai_provider TEXT,
            source TEXT DEFAULT 'recommendation',
            times_cooked INTEGER DEFAULT 0,
            last_cooked TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create recipe_ratings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ratings (
            id TEXT PRIMARY KEY,
            recipe_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            would_make_again BOOLEAN DEFAULT TRUE,
            cooking_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES saved_recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create meal_reviews table (for meal plan reviews)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_reviews (
            id TEXT PRIMARY KEY,
            meal_plan_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            would_make_again BOOLEAN DEFAULT TRUE,
            preparation_notes TEXT,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialization complete")
        
        # Verify the schema was created correctly
        if not verify_database_schema():
            logger.error("❌ Database schema verification failed after initialization")
            raise RuntimeError("Database schema verification failed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def populate_sample_data():
    """Populate database with sample ingredients and test data"""
    logger.info("🌱 Adding sample data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sample ingredients
    ingredients = [
        ("chicken-breast", "Chicken Breast", "Meat", "pound", 231, 43.5, 0, 5.0, '["dairy"]'),
        ("ground-beef", "Ground Beef", "Meat", "pound", 250, 26, 0, 17, '[]'),
        ("salmon", "Salmon", "Fish", "pound", 206, 22, 0, 12, '["fish"]'),
        ("white-rice", "White Rice", "Grain", "cup", 205, 4.2, 45, 0.4, '[]'),
        ("brown-rice", "Brown Rice", "Grain", "cup", 216, 5, 45, 1.8, '[]'),
        ("pasta", "Pasta", "Grain", "cup", 220, 8, 44, 1.1, '["gluten"]'),
        ("broccoli", "Broccoli", "Vegetable", "cup", 25, 3, 5, 0.3, '[]'),
        ("carrots", "Carrots", "Vegetable", "cup", 52, 1.2, 12, 0.2, '[]'),
        ("spinach", "Spinach", "Vegetable", "cup", 7, 0.9, 1.1, 0.1, '[]'),
        ("tomatoes", "Tomatoes", "Vegetable", "cup", 32, 1.6, 7, 0.4, '[]'),
        ("onions", "Onions", "Vegetable", "cup", 64, 1.8, 15, 0.2, '[]'),
        ("garlic", "Garlic", "Vegetable", "clove", 4, 0.2, 1, 0, '[]'),
        ("olive-oil", "Olive Oil", "Oil", "tablespoon", 119, 0, 0, 13.5, '[]'),
        ("butter", "Butter", "Dairy", "tablespoon", 102, 0.1, 0, 11.5, '["dairy"]'),
        ("milk", "Milk", "Dairy", "cup", 149, 8, 12, 8, '["dairy"]'),
        ("eggs", "Eggs", "Protein", "piece", 70, 6, 0.6, 5, '["eggs"]'),
        ("cheese", "Cheese", "Dairy", "ounce", 113, 7, 1, 9, '["dairy"]'),
        ("bread", "Bread", "Grain", "slice", 79, 2.7, 14, 1.2, '["gluten"]'),
        ("potatoes", "Potatoes", "Vegetable", "cup", 134, 3, 31, 0.2, '[]'),
        ("bell-peppers", "Bell Peppers", "Vegetable", "cup", 30, 1, 7, 0.3, '[]')
    ]
    
    for ingredient in ingredients:
        cursor.execute('''
            INSERT OR IGNORE INTO ingredients (id, name, category, unit, calories_per_unit, protein_per_unit, carbs_per_unit, fat_per_unit, allergens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ingredient)
    
    conn.commit()
    conn.close()
    logger.info("✅ Sample data added")