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
    logger.info(f"🗄️ Using database: {db_path} (Environment: {settings.ENVIRONMENT})")
    return db_path


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor, conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        conn.close()


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
            recipe_name TEXT,
            recipe_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialization complete")


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