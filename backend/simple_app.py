from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
import sqlite3
import hashlib
import jwt
import datetime
import uuid
import os
import logging
from dotenv import load_dotenv
from ai_service import ai_service
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Food Planning API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://food-planning-app.vercel.app",
        "https://food-planning-app-git-master-sams-projects-c6bbe2f2.vercel.app",
        "https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app",
        "https://*.vercel.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def get_db_connection():
    """Get database connection - PostgreSQL if DATABASE_URL exists, otherwise SQLite"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Use PostgreSQL
        return psycopg2.connect(database_url)
    else:
        # Fall back to SQLite for local development
        db_path = os.environ.get('DATABASE_PATH', 'simple_food_app.db')
        return sqlite3.connect(db_path)

def get_db_path():
    """Get database path based on environment with multiple detection methods"""
    # Enhanced environment detection for Railway with fallback methods
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT_NAME', '').lower()
    railway_service = os.environ.get('RAILWAY_SERVICE_NAME', '')
    railway_project = os.environ.get('RAILWAY_PROJECT_NAME', '')
    railway_deployment_id = os.environ.get('RAILWAY_DEPLOYMENT_ID', '')
    
    # Additional detection methods
    port = os.environ.get('PORT', '')
    
    # Check if we're on Railway
    is_railway = any([railway_env, railway_service, railway_project, railway_deployment_id])
    
    # Create a unique database identifier based on multiple factors
    env_identifier = 'local'
    
    print(f"🔍 ROBUST DB PATH DETERMINATION:")
    print(f"   - RAILWAY_ENVIRONMENT_NAME: {os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'NOT_SET')}")
    print(f"   - RAILWAY_SERVICE_NAME: {os.environ.get('RAILWAY_SERVICE_NAME', 'NOT_SET')}")
    print(f"   - RAILWAY_PROJECT_NAME: {os.environ.get('RAILWAY_PROJECT_NAME', 'NOT_SET')}")
    print(f"   - RAILWAY_DEPLOYMENT_ID: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'NOT_SET')}")
    print(f"   - PORT: {port}")
    print(f"   - Is Railway: {is_railway}")
    
    if is_railway:
        # Method 1: Direct environment name
        if railway_env == 'preview':
            env_identifier = 'preview'
        elif railway_env == 'production':
            env_identifier = 'production'
        # Method 2: Service name contains environment
        elif 'preview' in railway_service.lower():
            env_identifier = 'preview'
        elif 'production' in railway_service.lower():
            env_identifier = 'production'
        # Method 3: Deployment ID pattern (if Railway uses patterns)
        elif railway_deployment_id:
            if 'preview' in railway_deployment_id.lower():
                env_identifier = 'preview'
            elif 'prod' in railway_deployment_id.lower():
                env_identifier = 'production'
            else:
                # Use deployment ID as part of path to ensure uniqueness
                env_identifier = f"railway_{railway_deployment_id[:8]}"
        else:
            # Fallback: create unique identifier from service name
            env_identifier = f"railway_{railway_service.lower()}" if railway_service else 'railway_unknown'
    
    # Generate database path
    if env_identifier == 'preview':
        db_path = '/app/data/preview_food_app.db'
    elif env_identifier == 'production':
        db_path = '/app/data/production_food_app.db'
    elif env_identifier == 'local':
        db_path = os.environ.get('DATABASE_PATH', 'simple_food_app.db')
    else:
        # Railway environment with unique identifier
        db_path = f'/app/data/{env_identifier}_food_app.db'
    
    print(f"   - Environment identifier: {env_identifier}")
    print(f"   - Selected database path: {db_path}")
    return db_path

def init_db():
    db_path = get_db_path()
    
    # Ensure directory exists with proper error handling
    try:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            print(f"📁 Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
            # Check if directory was created successfully
            if not os.path.exists(db_dir):
                print(f"❌ Failed to create directory: {db_dir}")
                raise Exception(f"Could not create database directory: {db_dir}")
            print(f"✅ Directory exists: {db_dir}")
    except Exception as e:
        print(f"❌ Directory creation error: {e}")
        raise
    
    # Try to connect to database
    try:
        print(f"🔗 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        print(f"✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print(f"   - Database path: {db_path}")
        print(f"   - Directory exists: {os.path.exists(os.path.dirname(db_path))}")
        print(f"   - Directory writable: {os.access(os.path.dirname(db_path), os.W_OK) if os.path.exists(os.path.dirname(db_path)) else 'N/A'}")
        raise
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            name TEXT,
            timezone TEXT DEFAULT 'UTC',
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            dietary_restrictions TEXT DEFAULT '[]',
            preferences TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
            meal_name TEXT NOT NULL,
            meal_description TEXT,
            recipe_data TEXT,
            ai_generated BOOLEAN DEFAULT 0,
            ai_provider TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date, meal_type)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_reviews (
            id TEXT PRIMARY KEY,
            meal_plan_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            would_make_again BOOLEAN DEFAULT 1,
            preparation_notes TEXT,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert sample ingredients - comprehensive list
    sample_ingredients = [
        # Original ingredients
        ('ing-1', 'Chicken Breast', 'Meat', 'pound', 231, 43.5, 0, 5, '[]'),
        ('ing-2', 'Rice', 'Grain', 'cup', 205, 4.3, 45, 0.4, '[]'),
        ('ing-3', 'Broccoli', 'Vegetable', 'cup', 25, 3, 5, 0.3, '[]'),
        ('ing-4', 'Olive Oil', 'Fat', 'tablespoon', 119, 0, 0, 13.5, '[]'),
        ('ing-5', 'Onion', 'Vegetable', 'medium', 44, 1.2, 10.3, 0.1, '[]'),
        ('ing-6', 'Garlic', 'Vegetable', 'clove', 4, 0.2, 1, 0, '[]'),
        ('ing-7', 'Tomato', 'Vegetable', 'medium', 22, 1.1, 4.8, 0.2, '[]'),
        ('ing-8', 'Beef Ground', 'Meat', 'pound', 332, 30, 0, 23, '[]'),
        ('ing-9', 'Milk', 'Dairy', 'cup', 146, 8, 11, 8, '["lactose"]'),
        ('ing-10', 'Eggs', 'Dairy', 'large', 70, 6.3, 0.4, 4.8, '[]'),
        ('ing-11', 'Flour', 'Grain', 'cup', 455, 13, 95, 1.2, '["gluten"]'),
        ('ing-12', 'Pasta', 'Grain', 'cup', 220, 8, 44, 1.1, '["gluten"]'),
        ('ing-13', 'Cheese Cheddar', 'Dairy', 'cup', 455, 28, 3.7, 37, '["lactose"]'),
        ('ing-14', 'Salmon', 'Fish', 'fillet', 206, 22, 0, 12, '[]'),
        ('ing-15', 'Spinach', 'Vegetable', 'cup', 7, 0.9, 1.1, 0.1, '[]'),
        ('ing-16', 'Carrots', 'Vegetable', 'cup', 52, 1.2, 12, 0.3, '[]'),
        ('ing-17', 'Potatoes', 'Vegetable', 'medium', 161, 4.3, 37, 0.2, '[]'),
        ('ing-18', 'Bell Pepper', 'Vegetable', 'medium', 24, 1, 7, 0.2, '[]'),
        ('ing-19', 'Mushrooms', 'Vegetable', 'cup', 15, 2.2, 2.3, 0.2, '[]'),
        ('ing-20', 'Bread', 'Grain', 'slice', 79, 2.7, 14, 1.1, '["gluten"]'),
        
        # Additional Vegetables
        ('ing-21', 'Cucumber', 'Vegetable', 'medium', 16, 0.7, 4, 0.1, '[]'),
        ('ing-22', 'Lettuce', 'Vegetable', 'cup', 5, 0.5, 1, 0.1, '[]'),
        ('ing-23', 'Celery', 'Vegetable', 'stalk', 6, 0.3, 1.2, 0.1, '[]'),
        ('ing-24', 'Zucchini', 'Vegetable', 'medium', 20, 1.5, 4, 0.3, '[]'),
        ('ing-25', 'Eggplant', 'Vegetable', 'medium', 35, 1.4, 8.6, 0.2, '[]'),
        ('ing-26', 'Asparagus', 'Vegetable', 'spear', 3, 0.3, 0.6, 0, '[]'),
        ('ing-27', 'Green Beans', 'Vegetable', 'cup', 35, 2, 8, 0.1, '[]'),
        ('ing-28', 'Corn', 'Vegetable', 'cup', 132, 4.7, 29, 1.8, '[]'),
        ('ing-29', 'Sweet Potato', 'Vegetable', 'medium', 112, 2, 26, 0.1, '[]'),
        ('ing-30', 'Cauliflower', 'Vegetable', 'cup', 25, 2, 5, 0.3, '[]'),
        ('ing-31', 'Brussels Sprouts', 'Vegetable', 'cup', 38, 3, 8, 0.3, '[]'),
        ('ing-32', 'Kale', 'Vegetable', 'cup', 33, 2.9, 7, 0.6, '[]'),
        ('ing-33', 'Avocado', 'Vegetable', 'medium', 234, 2.9, 12, 21, '[]'),
        ('ing-34', 'Beets', 'Vegetable', 'medium', 35, 1.3, 8, 0.1, '[]'),
        ('ing-35', 'Radish', 'Vegetable', 'cup', 19, 0.8, 4, 0.1, '[]'),
        
        # Additional Fruits
        ('ing-36', 'Apple', 'Fruit', 'medium', 95, 0.5, 25, 0.3, '[]'),
        ('ing-37', 'Banana', 'Fruit', 'medium', 105, 1.3, 27, 0.4, '[]'),
        ('ing-38', 'Orange', 'Fruit', 'medium', 62, 1.2, 15, 0.2, '[]'),
        ('ing-39', 'Strawberries', 'Fruit', 'cup', 49, 1, 12, 0.5, '[]'),
        ('ing-40', 'Blueberries', 'Fruit', 'cup', 84, 1.1, 21, 0.5, '[]'),
        ('ing-41', 'Grapes', 'Fruit', 'cup', 104, 1.1, 27, 0.2, '[]'),
        ('ing-42', 'Lemon', 'Fruit', 'medium', 17, 0.6, 5, 0.2, '[]'),
        ('ing-43', 'Lime', 'Fruit', 'medium', 20, 0.5, 7, 0.1, '[]'),
        ('ing-44', 'Pineapple', 'Fruit', 'cup', 82, 0.9, 22, 0.2, '[]'),
        ('ing-45', 'Mango', 'Fruit', 'cup', 107, 1.4, 28, 0.4, '[]'),
        
        # Additional Meats
        ('ing-46', 'Chicken Thighs', 'Meat', 'pound', 250, 26, 0, 15, '[]'),
        ('ing-47', 'Turkey Breast', 'Meat', 'pound', 189, 29, 0, 7, '[]'),
        ('ing-48', 'Pork Chops', 'Meat', 'pound', 231, 25, 0, 14, '[]'),
        ('ing-49', 'Beef Steak', 'Meat', 'pound', 271, 26, 0, 18, '[]'),
        ('ing-50', 'Bacon', 'Meat', 'slice', 43, 3, 0.1, 3.3, '[]'),
        ('ing-51', 'Ham', 'Meat', 'slice', 46, 5.5, 1.5, 2, '[]'),
        ('ing-52', 'Lamb', 'Meat', 'pound', 294, 25, 0, 21, '[]'),
        
        # Additional Fish & Seafood
        ('ing-53', 'Tuna', 'Fish', 'can', 191, 25, 0, 9, '[]'),
        ('ing-54', 'Cod', 'Fish', 'fillet', 189, 41, 0, 1.5, '[]'),
        ('ing-55', 'Shrimp', 'Fish', 'cup', 144, 28, 1, 2, '["shellfish"]'),
        ('ing-56', 'Crab', 'Fish', 'cup', 134, 27, 0, 2, '["shellfish"]'),
        ('ing-57', 'Lobster', 'Fish', 'cup', 129, 27, 1, 1, '["shellfish"]'),
        ('ing-58', 'Tilapia', 'Fish', 'fillet', 128, 26, 0, 3, '[]'),
        ('ing-59', 'Mahi Mahi', 'Fish', 'fillet', 134, 27, 0, 1, '[]'),
        
        # Additional Dairy
        ('ing-60', 'Greek Yogurt', 'Dairy', 'cup', 130, 23, 9, 0, '["lactose"]'),
        ('ing-61', 'Butter', 'Dairy', 'tablespoon', 102, 0.1, 0, 11.5, '["lactose"]'),
        ('ing-62', 'Cream Cheese', 'Dairy', 'ounce', 99, 2, 2, 10, '["lactose"]'),
        ('ing-63', 'Mozzarella', 'Dairy', 'cup', 336, 25, 2.5, 25, '["lactose"]'),
        ('ing-64', 'Parmesan', 'Dairy', 'ounce', 110, 10, 1, 7, '["lactose"]'),
        ('ing-65', 'Heavy Cream', 'Dairy', 'cup', 821, 5, 7, 88, '["lactose"]'),
        ('ing-66', 'Sour Cream', 'Dairy', 'cup', 444, 5, 9, 45, '["lactose"]'),
        
        # Additional Grains & Carbs
        ('ing-67', 'Quinoa', 'Grain', 'cup', 222, 8, 39, 4, '[]'),
        ('ing-68', 'Brown Rice', 'Grain', 'cup', 216, 5, 45, 2, '[]'),
        ('ing-69', 'Oats', 'Grain', 'cup', 307, 11, 55, 6, '[]'),
        ('ing-70', 'Barley', 'Grain', 'cup', 193, 4, 44, 1, '[]'),
        ('ing-71', 'Couscous', 'Grain', 'cup', 176, 6, 36, 0.3, '["gluten"]'),
        ('ing-72', 'Whole Wheat Bread', 'Grain', 'slice', 69, 4, 12, 1, '["gluten"]'),
        ('ing-73', 'Bagel', 'Grain', 'medium', 245, 10, 48, 2, '["gluten"]'),
        ('ing-74', 'Tortilla', 'Grain', 'medium', 159, 4, 26, 4, '["gluten"]'),
        
        # Legumes & Beans
        ('ing-75', 'Black Beans', 'Legume', 'cup', 227, 15, 41, 1, '[]'),
        ('ing-76', 'Kidney Beans', 'Legume', 'cup', 225, 15, 40, 1, '[]'),
        ('ing-77', 'Chickpeas', 'Legume', 'cup', 269, 15, 45, 4, '[]'),
        ('ing-78', 'Lentils', 'Legume', 'cup', 230, 18, 40, 1, '[]'),
        ('ing-79', 'Pinto Beans', 'Legume', 'cup', 245, 15, 45, 1, '[]'),
        ('ing-80', 'Navy Beans', 'Legume', 'cup', 255, 15, 47, 1, '[]'),
        
        # Nuts & Seeds
        ('ing-81', 'Almonds', 'Nuts', 'ounce', 164, 6, 6, 14, '["tree nuts"]'),
        ('ing-82', 'Walnuts', 'Nuts', 'ounce', 185, 4, 4, 18, '["tree nuts"]'),
        ('ing-83', 'Peanuts', 'Nuts', 'ounce', 161, 7, 5, 14, '["peanuts"]'),
        ('ing-84', 'Cashews', 'Nuts', 'ounce', 157, 5, 9, 12, '["tree nuts"]'),
        ('ing-85', 'Sunflower Seeds', 'Nuts', 'ounce', 165, 6, 6, 14, '[]'),
        ('ing-86', 'Chia Seeds', 'Nuts', 'ounce', 137, 5, 12, 9, '[]'),
        ('ing-87', 'Flax Seeds', 'Nuts', 'tablespoon', 37, 1.3, 2, 3, '[]'),
        
        # Herbs & Spices
        ('ing-88', 'Basil', 'Herb', 'tablespoon', 1, 0.1, 0.1, 0, '[]'),
        ('ing-89', 'Oregano', 'Herb', 'tablespoon', 3, 0.1, 0.7, 0.1, '[]'),
        ('ing-90', 'Thyme', 'Herb', 'tablespoon', 3, 0.1, 0.8, 0.1, '[]'),
        ('ing-91', 'Rosemary', 'Herb', 'tablespoon', 2, 0.1, 0.4, 0.1, '[]'),
        ('ing-92', 'Cilantro', 'Herb', 'tablespoon', 1, 0.1, 0.1, 0, '[]'),
        ('ing-93', 'Parsley', 'Herb', 'tablespoon', 1, 0.1, 0.2, 0, '[]'),
        ('ing-94', 'Cumin', 'Spice', 'tablespoon', 22, 1, 3, 1, '[]'),
        ('ing-95', 'Paprika', 'Spice', 'tablespoon', 20, 1, 4, 1, '[]'),
        ('ing-96', 'Black Pepper', 'Spice', 'tablespoon', 17, 0.7, 4, 0.2, '[]'),
        ('ing-97', 'Salt', 'Spice', 'tablespoon', 0, 0, 0, 0, '[]'),
        ('ing-98', 'Ginger', 'Spice', 'tablespoon', 4, 0.1, 1, 0, '[]'),
        ('ing-99', 'Turmeric', 'Spice', 'tablespoon', 24, 1, 4, 1, '[]'),
        ('ing-100', 'Cinnamon', 'Spice', 'tablespoon', 19, 0.3, 6, 0.1, '[]')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO ingredients 
        (id, name, category, unit, calories_per_unit, protein_per_unit, carbs_per_unit, fat_per_unit, allergens)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_ingredients)
    
    conn.commit()
    conn.close()

def create_admin_user():
    """Create admin user after hash_password function is defined"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    admin_id = 'admin-user-id'
    admin_email = 'admin'
    admin_password = hash_password('admin123')  # Changed to 8 characters
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, email, hashed_password, name, is_admin, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (admin_id, admin_email, admin_password, 'Administrator', 1, 1))
    
    conn.commit()
    conn.close()

def populate_test_data():
    """Populate test data only in preview environment"""
    # Enhanced environment detection for Railway
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT_NAME', '').lower()
    railway_service = os.environ.get('RAILWAY_SERVICE_NAME', '')
    is_preview = railway_env == 'preview' or 'preview' in railway_service.lower()
    
    print(f"🔍 TEST DATA POPULATION ANALYSIS:")
    print(f"   - RAILWAY_ENVIRONMENT_NAME: {os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'NOT_SET')}")
    print(f"   - RAILWAY_SERVICE_NAME: {os.environ.get('RAILWAY_SERVICE_NAME', 'NOT_SET')}")
    print(f"   - Is Preview: {is_preview}")
    print(f"   - Database path: {get_db_path()}")
    
    # Log all Railway environment variables
    railway_vars = {k: v for k, v in os.environ.items() if 'railway' in k.lower()}
    print(f"   - All Railway env vars: {railway_vars}")
    
    if not is_preview:
        print(f"❌ Skipping test data - not in preview environment")
        return  # Only populate test data in preview
    
    print("📊 Starting test data population for preview environment...")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create admin user for preview
    admin_id = 'admin-user-id'
    admin_email = 'admin'
    admin_password = hash_password('admin123')
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, email, hashed_password, name, is_admin, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (admin_id, admin_email, admin_password, 'Administrator', 1, 1))
    
    print("✅ Admin user created/updated in preview environment")
    
    # Create test user
    test_user_id = 'test-user-123'
    test_email = 'test@example.com'
    test_password = hash_password('password123')
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, email, hashed_password, name, timezone, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (test_user_id, test_email, test_password, 'Test User', 'UTC', 1))
    
    # Create test family members
    family_members = [
        ('family-1', test_user_id, 'John Doe', 35, '["Vegetarian"]', '{"likes": ["pasta", "salad"], "dislikes": ["spicy food"], "preferred_cuisines": ["Italian", "Mediterranean"]}'),
        ('family-2', test_user_id, 'Jane Doe', 32, '["Gluten-Free"]', '{"likes": ["chicken", "vegetables"], "dislikes": ["seafood"], "preferred_cuisines": ["American", "Asian"]}'),
        ('family-3', test_user_id, 'Little Bobby', 8, '["Nut-Free"]', '{"likes": ["pizza", "chicken nuggets"], "dislikes": ["vegetables"], "preferred_cuisines": ["American"]}')
    ]
    
    for member in family_members:
        cursor.execute('''
            INSERT OR IGNORE INTO family_members (id, user_id, name, age, dietary_restrictions, preferences, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', member)
    
    # Create test pantry items (using actual ingredient IDs)
    pantry_items = [
        (test_user_id, 'ing-1', 2.0, None),  # Chicken Breast
        (test_user_id, 'ing-2', 1.0, None),  # Rice
        (test_user_id, 'ing-3', 1.0, None),  # Broccoli
        (test_user_id, 'ing-4', 1.0, None),  # Olive Oil
        (test_user_id, 'ing-5', 2.0, None)   # Onion
    ]
    
    for item in pantry_items:
        cursor.execute('''
            INSERT OR IGNORE INTO pantry_items (user_id, ingredient_id, quantity, expiration_date, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', item)
    
    conn.commit()
    conn.close()
    print(f"✅ Test data populated for preview environment")

init_db()

# Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Allow 'admin' as a special case
        if v == 'admin':
            return v
        # Otherwise validate as email using simple regex
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, v):
            return v
        raise ValueError('Invalid email format')

class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Allow 'admin' as a special case
        if v == 'admin':
            return v
        # Otherwise validate as email using simple regex
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, v):
            return v
        raise ValueError('Invalid email format')

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool = True
    is_admin: bool = False
    created_at: str

class FamilyMemberCreate(BaseModel):
    name: str
    age: Optional[int] = None
    dietary_restrictions: Optional[list] = []
    preferences: Optional[dict] = {}

class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    dietary_restrictions: Optional[list] = None
    preferences: Optional[dict] = None

class FamilyMemberResponse(BaseModel):
    id: str
    user_id: str
    name: str
    age: Optional[int] = None
    dietary_restrictions: list = []
    preferences: dict = {}
    created_at: str

class IngredientResponse(BaseModel):
    id: str
    name: str
    category: str
    unit: str
    calories_per_unit: float = 0
    protein_per_unit: float = 0
    carbs_per_unit: float = 0
    fat_per_unit: float = 0
    allergens: list = []
    created_at: str

class PantryItemCreate(BaseModel):
    ingredient_id: str
    quantity: float
    expiration_date: Optional[str] = None

class PantryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    expiration_date: Optional[str] = None

class PantryItemResponse(BaseModel):
    user_id: str
    ingredient_id: str
    ingredient: IngredientResponse
    quantity: float
    expiration_date: Optional[str] = None
    updated_at: str

class MealRecommendationRequest(BaseModel):
    num_recommendations: Optional[int] = 5
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    preferences: Optional[dict] = {}
    ai_provider: Optional[str] = "claude"  # claude or groq

class MealRecommendationResponse(BaseModel):
    name: str
    description: str
    prep_time: int
    difficulty: str
    servings: int
    ingredients_needed: list
    instructions: list
    tags: list
    nutrition_notes: str
    pantry_usage_score: int
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None

class MealPlanCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    meal_type: str  # breakfast, lunch, dinner, snack
    meal_name: str
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None

class MealPlanUpdate(BaseModel):
    meal_name: Optional[str] = None
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None

class MealPlanResponse(BaseModel):
    id: str
    user_id: str
    date: str
    meal_type: str
    meal_name: str
    meal_description: Optional[str] = None
    recipe_data: Optional[dict] = None
    ai_generated: bool = False
    ai_provider: Optional[str] = None
    created_at: str

class MealReviewCreate(BaseModel):
    rating: int  # 1-5 stars
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = True
    preparation_notes: Optional[str] = None

class MealReviewUpdate(BaseModel):
    rating: Optional[int] = None
    review_text: Optional[str] = None
    would_make_again: Optional[bool] = None
    preparation_notes: Optional[str] = None

class MealReviewResponse(BaseModel):
    id: str
    meal_plan_id: str
    user_id: str
    rating: int
    review_text: Optional[str] = None
    would_make_again: bool = True
    preparation_notes: Optional[str] = None
    reviewed_at: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(user_id: str) -> str:
    payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, 'secret', algorithm='HS256')

def verify_token(token: str):
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        return payload['sub']
    except:
        return None

# Auth dependency
def get_current_user_dependency(authorization: str = Header(None)):
    """FastAPI dependency for getting current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, timezone, is_active, is_admin, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            'id': user[0],
            'email': user[1], 
            'name': user[2],
            'timezone': user[3],
            'is_active': bool(user[4]),
            'is_admin': bool(user[5]),
            'created_at': user[6]
        }
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=401, detail="Authentication failed")

def get_current_user(authorization: str = None):
    """Helper function for legacy endpoints"""
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        user_id = verify_token(token)
        if not user_id:
            return None
            
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, timezone, is_active, is_admin, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
            
        return {
            'id': user[0],
            'email': user[1], 
            'name': user[2],
            'timezone': user[3],
            'is_active': bool(user[4]),
            'is_admin': bool(user[5]),
            'created_at': user[6]
        }
    except:
        return None

# Create admin user and populate test data after functions are defined
create_admin_user()
populate_test_data()

# Routes
@app.get("/")
async def root():
    return {"message": "Food Planning App API"}

@app.get("/api/v1/debug/check-admin")
async def check_admin():
    """Debug endpoint to check admin user status"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, hashed_password, is_admin, is_active FROM users WHERE email = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        test_password = hash_password('admin123')
        return {
            "admin_exists": True,
            "admin_id": admin[0],
            "is_admin": bool(admin[3]),
            "is_active": bool(admin[4]),
            "password_match": admin[2] == test_password,
            "db_path": get_db_path()
        }
    else:
        return {
            "admin_exists": False,
            "db_path": get_db_path()
        }
    
    conn.close()

@app.post("/api/v1/debug/test-admin-login")
async def test_admin_login():
    """Test the complete admin login flow"""
    # Test login
    login_data = UserLogin(email="admin", password="admin123")
    try:
        token_response = await login(login_data)
        
        # Test token verification
        test_user_id = verify_token(token_response.access_token)
        
        # Get user details
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, is_admin, is_active FROM users WHERE id = ?", (test_user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return {
            "login_success": True,
            "token_created": bool(token_response.access_token),
            "token_valid": bool(test_user_id),
            "user_found": bool(user),
            "user_details": {
                "id": user[0] if user else None,
                "email": user[1] if user else None,
                "is_admin": bool(user[2]) if user else None,
                "is_active": bool(user[3]) if user else None
            } if user else None
        }
    except Exception as e:
        return {
            "login_success": False,
            "error": str(e)
        }

@app.get("/api/v1/debug/admin-test")
async def debug_admin_test():
    """Debug endpoint to test admin user existence and authentication"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if admin user exists
    cursor.execute("SELECT id, email, hashed_password, name, is_admin FROM users WHERE email = 'admin'")
    admin_user = cursor.fetchone()
    
    if not admin_user:
        conn.close()
        return {"status": "ADMIN_NOT_FOUND", "message": "Admin user does not exist in database"}
    
    # Test password verification
    test_password = "admin123"
    password_valid = verify_password(test_password, admin_user[2])
    
    conn.close()
    
    return {
        "status": "SUCCESS",
        "admin_exists": True,
        "admin_id": admin_user[0],
        "admin_email": admin_user[1],
        "admin_name": admin_user[3],
        "is_admin": bool(admin_user[4]),
        "password_valid": password_valid,
        "test_password": test_password,
        "db_path": get_db_path()
    }

@app.get("/health")
async def health():
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'NOT_SET')
    railway_service = os.environ.get('RAILWAY_SERVICE_NAME', 'NOT_SET')
    railway_project = os.environ.get('RAILWAY_PROJECT_NAME', 'NOT_SET')
    db_path = get_db_path()
    
    # Get all environment variables for debugging
    all_env_vars = {k: v for k, v in os.environ.items() if any(keyword in k.lower() for keyword in ['railway', 'env', 'prod', 'preview'])}
    
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": {
            "railway_environment_name": railway_env,
            "railway_service_name": railway_service,
            "railway_project_name": railway_project,
            "detected_db_path": db_path,
            "is_railway": any([railway_env != 'NOT_SET', railway_service != 'NOT_SET', railway_project != 'NOT_SET']),
            "all_relevant_env_vars": all_env_vars
        },
        "db_separation": "enhanced_v2",
        "deployment_info": {
            "git_commit": os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')[:8],
            "deployment_id": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')
        }
    }

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    cursor.execute(
        "INSERT INTO users (id, email, hashed_password, name) VALUES (?, ?, ?, ?)",
        (user_id, user_data.email, hashed_password, user_data.name)
    )
    conn.commit()
    conn.close()
    
    # Create tokens
    access_token = create_token(user_id)
    refresh_token = create_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400
    )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    print(f"🔐 LOGIN ATTEMPT - Email: {user_data.email}")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, hashed_password, is_active, is_admin FROM users WHERE email = ?", (user_data.email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ LOGIN FAILED - User not found: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    print(f"📋 User found - ID: {user[0]}, Active: {user[2]}, Admin: {user[3]}")
    
    password_valid = verify_password(user_data.password, user[1])
    print(f"🔑 Password verification: {password_valid}")
    
    if not password_valid:
        print(f"❌ LOGIN FAILED - Invalid password for: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user[2]:  # Check is_active
        print(f"❌ LOGIN FAILED - Inactive user: {user_data.email}")
        conn.close()
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    conn.close()
    
    # Create tokens
    access_token = create_token(user[0])
    refresh_token = create_token(user[0])
    
    print(f"✅ LOGIN SUCCESS - User: {user_data.email}, Token created")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_endpoint(authorization: str = Header(None)):
    # Debug logging
    print(f"🔍 /auth/me called")
    print(f"📋 Authorization header present: {bool(authorization)}")
    
    if authorization:
        print(f"🔐 Auth header value (first 20 chars): {authorization[:20]}...")
    
    # If no authorization header, return 401
    if not authorization:
        print("❌ No authorization header provided")
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        current_user = get_current_user_dependency(authorization)
        print(f"✅ Authentication successful for user: {current_user['email']}")
        print(f"👤 User details - Admin: {current_user['is_admin']}, Active: {current_user['is_active']}")
        
        return UserResponse(
            id=current_user['id'],
            email=current_user['email'],
            name=current_user['name'],
            timezone=current_user['timezone'],
            is_active=current_user['is_active'],
            is_admin=current_user['is_admin'],
            created_at=current_user['created_at']
        )
    except HTTPException as e:
        print(f"❌ Authentication failed with HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        print(f"❌ Authentication failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.delete("/api/v1/auth/delete-account")
async def delete_user_account(authorization: str = Header(None)):
    """Delete current user account and all associated data"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = current_user['id']
    
    # Prevent admin account deletion for safety
    if current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Cannot delete admin account. Use admin panel to manage accounts.")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Delete user data in order (foreign key constraints)
        cursor.execute("DELETE FROM meal_reviews WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM pantry_items WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

# Family Members endpoints
@app.get("/api/v1/family/members", response_model=List[FamilyMemberResponse])
async def get_family_members(authorization: str = Header(None)):
    # Try to get authenticated user, fallback to admin
    try:
        if authorization:
            current_user = get_current_user_dependency(authorization)
            user_id = current_user['id']
            is_admin = current_user.get('is_admin', False)
        else:
            # Fallback to admin user
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_admin FROM users WHERE email = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            if admin_user:
                user_id = admin_user[0]
                is_admin = bool(admin_user[1])
            else:
                raise HTTPException(status_code=401, detail="No admin user found")
            cursor.close()
    except HTTPException:
        raise
    except:
        # Final fallback
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_admin FROM users WHERE email = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        if admin_user:
            user_id = admin_user[0]
            is_admin = bool(admin_user[1])
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
        cursor.close()
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Admin can see all family members, regular users only see their own
    if is_admin:
        cursor.execute(
            "SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at FROM family_members ORDER BY user_id, name"
        )
    else:
        cursor.execute(
            "SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at FROM family_members WHERE user_id = ?",
            (user_id,)
        )
    
    members = cursor.fetchall()
    conn.close()
    
    return [
        FamilyMemberResponse(
            id=member[0],
            user_id=member[1],
            name=member[2],
            age=member[3],
            dietary_restrictions=eval(member[4]) if member[4] else [],
            preferences=eval(member[5]) if member[5] else {},
            created_at=member[6]
        )
        for member in members
    ]

@app.post("/api/v1/family/members", response_model=FamilyMemberResponse)
async def create_family_member(member_data: FamilyMemberCreate, authorization: str = Header(None)):
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    member_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO family_members (id, user_id, name, age, dietary_restrictions, preferences) VALUES (?, ?, ?, ?, ?, ?)",
        (
            member_id,
            user_id,
            member_data.name,
            member_data.age,
            str(member_data.dietary_restrictions),
            str(member_data.preferences)
        )
    )
    conn.commit()
    
    # Get the created member
    cursor.execute(
        "SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at FROM family_members WHERE id = ?",
        (member_id,)
    )
    member = cursor.fetchone()
    conn.close()
    
    return FamilyMemberResponse(
        id=member[0],
        user_id=member[1],
        name=member[2],
        age=member[3],
        dietary_restrictions=eval(member[4]) if member[4] else [],
        preferences=eval(member[5]) if member[5] else {},
        created_at=member[6]
    )

@app.put("/api/v1/family/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(member_id: str, member_data: FamilyMemberUpdate):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if member exists
    cursor.execute("SELECT * FROM family_members WHERE id = ?", (member_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Family member not found")
    
    # Build update query dynamically
    updates = []
    values = []
    
    if member_data.name is not None:
        updates.append("name = ?")
        values.append(member_data.name)
    if member_data.age is not None:
        updates.append("age = ?")
        values.append(member_data.age)
    if member_data.dietary_restrictions is not None:
        updates.append("dietary_restrictions = ?")
        values.append(str(member_data.dietary_restrictions))
    if member_data.preferences is not None:
        updates.append("preferences = ?")
        values.append(str(member_data.preferences))
    
    if updates:
        values.append(member_id)
        cursor.execute(
            f"UPDATE family_members SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
    
    # Get updated member
    cursor.execute(
        "SELECT id, user_id, name, age, dietary_restrictions, preferences, created_at FROM family_members WHERE id = ?",
        (member_id,)
    )
    member = cursor.fetchone()
    conn.close()
    
    return FamilyMemberResponse(
        id=member[0],
        user_id=member[1],
        name=member[2],
        age=member[3],
        dietary_restrictions=eval(member[4]) if member[4] else [],
        preferences=eval(member[5]) if member[5] else {},
        created_at=member[6]
    )

@app.delete("/api/v1/family/members/{member_id}")
async def delete_family_member(member_id: str):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if member exists
    cursor.execute("SELECT * FROM family_members WHERE id = ?", (member_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Family member not found")
    
    cursor.execute("DELETE FROM family_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Family member deleted successfully"}

# Admin endpoints
@app.get("/api/v1/admin/users")
async def get_all_users():
    """Admin endpoint to view all users"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, email, name, timezone, is_active, is_admin, created_at, hashed_password
        FROM users 
        ORDER BY created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': user[0],
            'email': user[1],
            'name': user[2],
            'timezone': user[3],
            'is_active': bool(user[4]),
            'is_admin': bool(user[5]),
            'created_at': user[6],
            'hashed_password': user[7]
        }
        for user in users
    ]

@app.get("/api/v1/admin/family/all")
async def get_all_family_members():
    """Admin endpoint to view all family members across all users"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT fm.id, fm.user_id, fm.name, fm.age, fm.dietary_restrictions, fm.preferences, fm.created_at,
               u.email as user_email, u.name as user_name
        FROM family_members fm
        JOIN users u ON fm.user_id = u.id
        ORDER BY u.email, fm.name
    ''')
    family_members = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': member[0],
            'user_id': member[1],
            'name': member[2],
            'age': member[3],
            'dietary_restrictions': eval(member[4]) if member[4] else [],
            'preferences': eval(member[5]) if member[5] else {},
            'created_at': member[6],
            'user_email': member[7],
            'user_name': member[8]
        }
        for member in family_members
    ]

@app.get("/api/v1/admin/stats")
async def get_admin_stats():
    """Admin endpoint to get platform statistics"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get total users
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
    total_users = cursor.fetchone()[0]
    
    # Get total family members
    cursor.execute("SELECT COUNT(*) FROM family_members")
    total_family_members = cursor.fetchone()[0]
    
    # Get total pantry items
    cursor.execute("SELECT COUNT(*) FROM pantry_items")
    total_pantry_items = cursor.fetchone()[0]
    
    # Get recent registrations (last 30 days)
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE is_admin = 0 AND created_at >= datetime('now', '-30 days')
    """)
    recent_registrations = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_family_members': total_family_members,
        'total_pantry_items': total_pantry_items,
        'recent_registrations': recent_registrations
    }

# Admin User Management endpoints
@app.delete("/api/v1/admin/users/{user_id}")
async def admin_delete_user(user_id: str, authorization: str = Header(None)):
    """Admin endpoint to delete any user account"""
    # Check if current user is admin
    current_user = get_current_user(authorization)
    if not current_user or not current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent admin from deleting themselves
    if current_user['id'] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, email, is_admin FROM users WHERE id = ?", (user_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting other admin accounts for safety
    if target_user[2]:  # is_admin
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot delete other admin accounts")
    
    try:
        # Delete user data in order (foreign key constraints)
        cursor.execute("DELETE FROM meal_reviews WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM pantry_items WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": f"User account deleted successfully", "deleted_user_email": target_user[1]}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error deleting user account: {str(e)}")

class PasswordResetRequest(BaseModel):
    new_password: str

@app.post("/api/v1/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, request: PasswordResetRequest, authorization: str = Header(None)):
    """Admin endpoint to reset a user's password"""
    # Check if current user is admin
    current_user = get_current_user(authorization)
    if not current_user or not current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Hash the new password
        hashed_password = hash_password(request.new_password)
        
        # Update user's password
        cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (hashed_password, user_id))
        
        conn.commit()
        conn.close()
        
        return {"message": f"Password reset successfully for user", "user_email": target_user[1]}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")

# Ingredients endpoints
@app.get("/api/v1/ingredients", response_model=List[IngredientResponse])
async def get_ingredients():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, category, unit, calories_per_unit, protein_per_unit, 
               carbs_per_unit, fat_per_unit, allergens, created_at 
        FROM ingredients 
        ORDER BY category, name
    ''')
    ingredients = cursor.fetchall()
    conn.close()
    
    return [
        IngredientResponse(
            id=ingredient[0],
            name=ingredient[1],
            category=ingredient[2],
            unit=ingredient[3],
            calories_per_unit=ingredient[4] or 0,
            protein_per_unit=ingredient[5] or 0,
            carbs_per_unit=ingredient[6] or 0,
            fat_per_unit=ingredient[7] or 0,
            allergens=eval(ingredient[8]) if ingredient[8] else [],
            created_at=ingredient[9]
        )
        for ingredient in ingredients
    ]

@app.get("/api/v1/ingredients/search")
async def search_ingredients(q: str):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, category, unit, calories_per_unit, protein_per_unit, 
               carbs_per_unit, fat_per_unit, allergens, created_at 
        FROM ingredients 
        WHERE name LIKE ? 
        ORDER BY name
        LIMIT 20
    ''', (f'%{q}%',))
    ingredients = cursor.fetchall()
    conn.close()
    
    return [
        IngredientResponse(
            id=ingredient[0],
            name=ingredient[1],
            category=ingredient[2],
            unit=ingredient[3],
            calories_per_unit=ingredient[4] or 0,
            protein_per_unit=ingredient[5] or 0,
            carbs_per_unit=ingredient[6] or 0,
            fat_per_unit=ingredient[7] or 0,
            allergens=eval(ingredient[8]) if ingredient[8] else [],
            created_at=ingredient[9]
        )
        for ingredient in ingredients
    ]

# Pantry endpoints
@app.get("/api/v1/pantry", response_model=List[PantryItemResponse])
async def get_pantry_items(authorization: str = Header(None)):
    # Try to get authenticated user, fallback to admin
    try:
        if authorization:
            current_user = get_current_user_dependency(authorization)
            user_id = current_user['id']
        else:
            # Fallback to admin user
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            if admin_user:
                user_id = admin_user[0]
            else:
                raise HTTPException(status_code=401, detail="No admin user found")
            cursor.close()
    except HTTPException:
        raise
    except:
        # Final fallback
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        if admin_user:
            user_id = admin_user[0]
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
        cursor.close()
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
               i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
               i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
        FROM pantry_items p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.user_id = ?
        ORDER BY i.category, i.name
    ''', (user_id,))
    
    pantry_items = cursor.fetchall()
    conn.close()
    
    return [
        PantryItemResponse(
            user_id=item[0],
            ingredient_id=item[1],
            quantity=item[2],
            expiration_date=item[3],
            updated_at=item[4],
            ingredient=IngredientResponse(
                id=item[5],
                name=item[6],
                category=item[7],
                unit=item[8],
                calories_per_unit=item[9] or 0,
                protein_per_unit=item[10] or 0,
                carbs_per_unit=item[11] or 0,
                fat_per_unit=item[12] or 0,
                allergens=eval(item[13]) if item[13] else [],
                created_at=item[14]
            )
        )
        for item in pantry_items
    ]

@app.post("/api/v1/pantry", response_model=PantryItemResponse)
async def add_pantry_item(pantry_data: PantryItemCreate, authorization: str = Header(None)):
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Check if ingredient exists
    cursor.execute("SELECT * FROM ingredients WHERE id = ?", (pantry_data.ingredient_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    # Insert or update pantry item
    cursor.execute('''
        INSERT OR REPLACE INTO pantry_items (user_id, ingredient_id, quantity, expiration_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, pantry_data.ingredient_id, pantry_data.quantity, pantry_data.expiration_date))
    conn.commit()
    
    # Get the pantry item with ingredient details
    cursor.execute('''
        SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
               i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
               i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
        FROM pantry_items p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.user_id = ? AND p.ingredient_id = ?
    ''', (user_id, pantry_data.ingredient_id))
    
    item = cursor.fetchone()
    conn.close()
    
    return PantryItemResponse(
        user_id=item[0],
        ingredient_id=item[1],
        quantity=item[2],
        expiration_date=item[3],
        updated_at=item[4],
        ingredient=IngredientResponse(
            id=item[5],
            name=item[6],
            category=item[7],
            unit=item[8],
            calories_per_unit=item[9] or 0,
            protein_per_unit=item[10] or 0,
            carbs_per_unit=item[11] or 0,
            fat_per_unit=item[12] or 0,
            allergens=eval(item[13]) if item[13] else [],
            created_at=item[14]
        )
    )

@app.put("/api/v1/pantry/{ingredient_id}", response_model=PantryItemResponse)
async def update_pantry_item(ingredient_id: str, pantry_data: PantryItemUpdate, authorization: str = Header(None)):
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Check if pantry item exists
    cursor.execute("SELECT * FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Pantry item not found")
    
    # Build update query dynamically
    updates = []
    values = []
    
    if pantry_data.quantity is not None:
        updates.append("quantity = ?")
        values.append(pantry_data.quantity)
    if pantry_data.expiration_date is not None:
        updates.append("expiration_date = ?")
        values.append(pantry_data.expiration_date)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([user_id, ingredient_id])
        cursor.execute(
            f"UPDATE pantry_items SET {', '.join(updates)} WHERE user_id = ? AND ingredient_id = ?",
            values
        )
        conn.commit()
    
    # Get updated pantry item with ingredient details
    cursor.execute('''
        SELECT p.user_id, p.ingredient_id, p.quantity, p.expiration_date, p.updated_at,
               i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
               i.carbs_per_unit, i.fat_per_unit, i.allergens, i.created_at
        FROM pantry_items p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.user_id = ? AND p.ingredient_id = ?
    ''', (user_id, ingredient_id))
    
    item = cursor.fetchone()
    conn.close()
    
    return PantryItemResponse(
        user_id=item[0],
        ingredient_id=item[1],
        quantity=item[2],
        expiration_date=item[3],
        updated_at=item[4],
        ingredient=IngredientResponse(
            id=item[5],
            name=item[6],
            category=item[7],
            unit=item[8],
            calories_per_unit=item[9] or 0,
            protein_per_unit=item[10] or 0,
            carbs_per_unit=item[11] or 0,
            fat_per_unit=item[12] or 0,
            allergens=eval(item[13]) if item[13] else [],
            created_at=item[14]
        )
    )

@app.delete("/api/v1/pantry/{ingredient_id}")
async def remove_pantry_item(ingredient_id: str, authorization: str = Header(None)):
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Check if pantry item exists
    cursor.execute("SELECT * FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Pantry item not found")
    
    cursor.execute("DELETE FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", (user_id, ingredient_id))
    conn.commit()
    conn.close()
    
    return {"message": "Pantry item removed successfully"}

# Meal Recommendations endpoints
@app.post("/api/v1/recommendations", response_model=List[MealRecommendationResponse])
async def get_meal_recommendations(request: MealRecommendationRequest, authorization: str = Header(None)):
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    print(f"🎯 RECOMMENDATIONS REQUEST - {datetime.datetime.now()}")
    print(f"📝 Request: {request}")
    logger.info("=== RECOMMENDATIONS REQUEST RECEIVED ===")
    logger.info(f"Request: {request}")
    logger.info(f"Time: {datetime.datetime.now()}")
    logger.info("="*50)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Get family members
    cursor.execute('''
        SELECT id, name, age, dietary_restrictions, preferences 
        FROM family_members 
        WHERE user_id = ?
    ''', (user_id,))
    family_data = cursor.fetchall()
    
    family_members = [
        {
            'id': member[0],
            'name': member[1],
            'age': member[2],
            'dietary_restrictions': eval(member[3]) if member[3] else [],
            'preferences': eval(member[4]) if member[4] else {}
        }
        for member in family_data
    ]
    
    # Get pantry items
    cursor.execute('''
        SELECT p.quantity, p.expiration_date,
               i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
               i.carbs_per_unit, i.fat_per_unit, i.allergens
        FROM pantry_items p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.user_id = ?
    ''', (user_id,))
    pantry_data = cursor.fetchall()
    
    pantry_items = [
        {
            'quantity': item[0],
            'expiration_date': item[1],
            'ingredient': {
                'id': item[2],
                'name': item[3],
                'category': item[4],
                'unit': item[5],
                'calories_per_unit': item[6] or 0,
                'protein_per_unit': item[7] or 0,
                'carbs_per_unit': item[8] or 0,
                'fat_per_unit': item[9] or 0,
                'allergens': eval(item[10]) if item[10] else []
            }
        }
        for item in pantry_data
    ]
    
    conn.close()
    
    try:
        # Get recommendations from selected AI provider
        provider = request.ai_provider or "claude"
        logger.info(f"DEBUG: Getting {request.num_recommendations} recommendations from {provider}")
        logger.info(f"DEBUG: Family members: {len(family_members)}")
        logger.info(f"DEBUG: Pantry items: {len(pantry_items)}")
        
        recommendations = await ai_service.get_meal_recommendations(
            family_members=family_members,
            pantry_items=pantry_items,
            preferences=request.preferences,
            num_recommendations=request.num_recommendations,
            provider=provider
        )
        
        logger.info(f"DEBUG: Got {len(recommendations)} recommendations")
        if recommendations:
            logger.info(f"DEBUG: First recommendation: {recommendations[0].get('name', 'NO_NAME')}")
            logger.info(f"DEBUG: AI Generated: {recommendations[0].get('ai_generated', 'UNKNOWN')}")
            logger.info(f"DEBUG: Tags: {recommendations[0].get('tags', [])}")
        
        response_list = [
            MealRecommendationResponse(
                name=rec['name'],
                description=rec['description'],
                prep_time=rec['prep_time'],
                difficulty=rec['difficulty'],
                servings=rec['servings'],
                ingredients_needed=rec['ingredients_needed'],
                instructions=rec['instructions'],
                tags=rec['tags'],
                nutrition_notes=rec['nutrition_notes'],
                pantry_usage_score=rec['pantry_usage_score'],
                ai_generated=rec.get('ai_generated', False),
                ai_provider=rec.get('ai_provider')
            )
            for rec in recommendations
        ]
        
        logger.info(f"RESPONSE: Returning {len(response_list)} recommendations")
        if response_list:
            logger.info(f"RESPONSE: First AI flag: {response_list[0].ai_generated}")
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/api/v1/recommendations/status")
async def get_recommendation_status():
    """Check status of available AI providers"""
    logger.info("🔍 Frontend checking AI provider status")
    print("🔍 AI PROVIDER STATUS CHECK - Current time:", datetime.datetime.now())
    
    providers = ai_service.get_available_providers()
    available_providers = [name for name, available in providers.items() if available]
    
    return {
        "providers": providers,
        "available_providers": available_providers,
        "default_provider": "claude" if providers.get("claude") else ("groq" if providers.get("groq") else None),
        "message": f"Available AI providers: {', '.join(available_providers)}" if available_providers else "No AI providers configured"
    }

@app.get("/api/v1/recommendations/test")
async def test_ai_recommendations(provider: str = "claude"):
    """Test endpoint to verify AI provider is working"""
    try:
        if not ai_service.is_provider_available(provider):
            return {
                "status": "PROVIDER_UNAVAILABLE",
                "provider": provider,
                "message": f"AI provider '{provider}' is not available or configured"
            }
        
        # Quick test with minimal data
        recommendations = await ai_service.get_meal_recommendations(
            family_members=[],
            pantry_items=[],
            num_recommendations=1,
            provider=provider
        )
        
        if recommendations and recommendations[0].get('ai_generated', False):
            return {
                "status": "AI_WORKING",
                "provider": provider,
                "test_recipe": recommendations[0]['name'],
                "ai_generated": recommendations[0].get('ai_generated', False),
                "ai_provider": recommendations[0].get('ai_provider'),
                "message": f"{provider.title()} AI is generating recipes successfully"
            }
        else:
            return {
                "status": "NO_RESULTS", 
                "provider": provider,
                "test_recipe": recommendations[0]['name'] if recommendations else "None",
                "message": f"{provider.title()} returned no valid recommendations"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "provider": provider,
            "error": str(e),
            "message": f"Error testing {provider} AI recommendations"
        }

# Meal Plan endpoints
@app.get("/api/v1/meal-plans", response_model=List[MealPlanResponse])
async def get_meal_plans(start_date: Optional[str] = None, end_date: Optional[str] = None, authorization: str = Header(None)):
    """Get meal plans for current user, optionally filtered by date range"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Build query with optional date filtering
    if start_date and end_date:
        cursor.execute('''
            SELECT id, user_id, date, meal_type, meal_name, meal_description, 
                   recipe_data, ai_generated, ai_provider, created_at
            FROM meal_plans 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date, 
                CASE meal_type 
                    WHEN 'breakfast' THEN 1 
                    WHEN 'lunch' THEN 2 
                    WHEN 'dinner' THEN 3 
                    WHEN 'snack' THEN 4 
                END
        ''', (user_id, start_date, end_date))
    else:
        cursor.execute('''
            SELECT id, user_id, date, meal_type, meal_name, meal_description, 
                   recipe_data, ai_generated, ai_provider, created_at
            FROM meal_plans 
            WHERE user_id = ?
            ORDER BY date DESC, 
                CASE meal_type 
                    WHEN 'breakfast' THEN 1 
                    WHEN 'lunch' THEN 2 
                    WHEN 'dinner' THEN 3 
                    WHEN 'snack' THEN 4 
                END
        ''', (user_id,))
    
    meal_plans = cursor.fetchall()
    conn.close()
    
    return [
        MealPlanResponse(
            id=plan[0],
            user_id=plan[1],
            date=plan[2],
            meal_type=plan[3],
            meal_name=plan[4],
            meal_description=plan[5],
            recipe_data=eval(plan[6]) if plan[6] else None,
            ai_generated=bool(plan[7]),
            ai_provider=plan[8],
            created_at=plan[9]
        )
        for plan in meal_plans
    ]

@app.post("/api/v1/meal-plans", response_model=MealPlanResponse)
async def create_meal_plan(meal_plan_data: MealPlanCreate, authorization: str = Header(None)):
    """Create a new meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    meal_plan_id = str(uuid.uuid4())
    
    # Check if meal already exists for this slot
    cursor.execute(
        "SELECT id FROM meal_plans WHERE user_id = ? AND date = ? AND meal_type = ?",
        (user_id, meal_plan_data.date, meal_plan_data.meal_type)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Meal already planned for this time slot")
    
    # Insert new meal plan
    cursor.execute('''
        INSERT INTO meal_plans 
        (id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        meal_plan_id,
        user_id,
        meal_plan_data.date,
        meal_plan_data.meal_type,
        meal_plan_data.meal_name,
        meal_plan_data.meal_description,
        str(meal_plan_data.recipe_data) if meal_plan_data.recipe_data else None,
        meal_plan_data.ai_generated,
        meal_plan_data.ai_provider
    ))
    conn.commit()
    
    # Get the created meal plan
    cursor.execute('''
        SELECT id, user_id, date, meal_type, meal_name, meal_description, 
               recipe_data, ai_generated, ai_provider, created_at
        FROM meal_plans WHERE id = ?
    ''', (meal_plan_id,))
    meal_plan = cursor.fetchone()
    conn.close()
    
    return MealPlanResponse(
        id=meal_plan[0],
        user_id=meal_plan[1],
        date=meal_plan[2],
        meal_type=meal_plan[3],
        meal_name=meal_plan[4],
        meal_description=meal_plan[5],
        recipe_data=eval(meal_plan[6]) if meal_plan[6] else None,
        ai_generated=bool(meal_plan[7]),
        ai_provider=meal_plan[8],
        created_at=meal_plan[9]
    )

@app.put("/api/v1/meal-plans/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(meal_plan_id: str, meal_plan_data: MealPlanUpdate):
    """Update an existing meal plan"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if meal plan exists
    cursor.execute("SELECT user_id FROM meal_plans WHERE id = ?", (meal_plan_id,))
    meal_plan = cursor.fetchone()
    if not meal_plan:
        conn.close()
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Build update query dynamically
    updates = []
    values = []
    
    if meal_plan_data.meal_name is not None:
        updates.append("meal_name = ?")
        values.append(meal_plan_data.meal_name)
    if meal_plan_data.meal_description is not None:
        updates.append("meal_description = ?")
        values.append(meal_plan_data.meal_description)
    if meal_plan_data.recipe_data is not None:
        updates.append("recipe_data = ?")
        values.append(str(meal_plan_data.recipe_data))
    
    if updates:
        values.append(meal_plan_id)
        cursor.execute(
            f"UPDATE meal_plans SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
    
    # Get updated meal plan
    cursor.execute('''
        SELECT id, user_id, date, meal_type, meal_name, meal_description, 
               recipe_data, ai_generated, ai_provider, created_at
        FROM meal_plans WHERE id = ?
    ''', (meal_plan_id,))
    meal_plan = cursor.fetchone()
    conn.close()
    
    return MealPlanResponse(
        id=meal_plan[0],
        user_id=meal_plan[1],
        date=meal_plan[2],
        meal_type=meal_plan[3],
        meal_name=meal_plan[4],
        meal_description=meal_plan[5],
        recipe_data=eval(meal_plan[6]) if meal_plan[6] else None,
        ai_generated=bool(meal_plan[7]),
        ai_provider=meal_plan[8],
        created_at=meal_plan[9]
    )

@app.delete("/api/v1/meal-plans/{meal_plan_id}")
async def delete_meal_plan(meal_plan_id: str):
    """Delete a meal plan"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if meal plan exists
    cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_plan_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Delete meal plan and its reviews
    cursor.execute("DELETE FROM meal_reviews WHERE meal_plan_id = ?", (meal_plan_id,))
    cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_plan_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Meal plan deleted successfully"}

# Meal Review endpoints
@app.get("/api/v1/meal-plans/{meal_plan_id}/reviews", response_model=List[MealReviewResponse])
async def get_meal_reviews(meal_plan_id: str):
    """Get reviews for a specific meal plan"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, meal_plan_id, user_id, rating, review_text, 
               would_make_again, preparation_notes, reviewed_at
        FROM meal_reviews 
        WHERE meal_plan_id = ?
        ORDER BY reviewed_at DESC
    ''', (meal_plan_id,))
    
    reviews = cursor.fetchall()
    conn.close()
    
    return [
        MealReviewResponse(
            id=review[0],
            meal_plan_id=review[1],
            user_id=review[2],
            rating=review[3],
            review_text=review[4],
            would_make_again=bool(review[5]),
            preparation_notes=review[6],
            reviewed_at=review[7]
        )
        for review in reviews
    ]

@app.post("/api/v1/meal-plans/{meal_plan_id}/reviews", response_model=MealReviewResponse)
async def create_meal_review(meal_plan_id: str, review_data: MealReviewCreate, authorization: str = Header(None)):
    """Create a review for a meal plan"""
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    user_id = current_user['id']
    
    # Check if meal plan exists
    cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_plan_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Check if user already reviewed this meal
    cursor.execute(
        "SELECT id FROM meal_reviews WHERE meal_plan_id = ? AND user_id = ?",
        (meal_plan_id, user_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="You have already reviewed this meal")
    
    review_id = str(uuid.uuid4())
    
    # Insert new review
    cursor.execute('''
        INSERT INTO meal_reviews 
        (id, meal_plan_id, user_id, rating, review_text, would_make_again, preparation_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        review_id,
        meal_plan_id,
        user_id,
        review_data.rating,
        review_data.review_text,
        review_data.would_make_again,
        review_data.preparation_notes
    ))
    conn.commit()
    
    # Get the created review
    cursor.execute('''
        SELECT id, meal_plan_id, user_id, rating, review_text, 
               would_make_again, preparation_notes, reviewed_at
        FROM meal_reviews WHERE id = ?
    ''', (review_id,))
    review = cursor.fetchone()
    conn.close()
    
    return MealReviewResponse(
        id=review[0],
        meal_plan_id=review[1],
        user_id=review[2],
        rating=review[3],
        review_text=review[4],
        would_make_again=bool(review[5]),
        preparation_notes=review[6],
        reviewed_at=review[7]
    )

if __name__ == "__main__":
    import uvicorn
    # Railway uses PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Food Planning API on port {port}")
    print(f"📊 Health check endpoint: http://0.0.0.0:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")