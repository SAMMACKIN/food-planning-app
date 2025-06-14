from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
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
    """Get database path based on environment"""
    env = os.environ.get('RAILWAY_ENVIRONMENT', 'development').lower()
    
    if env == 'preview':
        return '/app/data/preview_food_app.db'
    elif env == 'production':
        return '/app/data/production_food_app.db'
    else:
        # Local development
        return os.environ.get('DATABASE_PATH', 'simple_food_app.db')

def init_db():
    db_path = get_db_path()
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True) if os.path.dirname(db_path) else None
    conn = sqlite3.connect(db_path)
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
    
    # Insert sample ingredients
    sample_ingredients = [
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
        ('ing-20', 'Bread', 'Grain', 'slice', 79, 2.7, 14, 1.1, '["gluten"]')
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
    admin_password = hash_password('admin')
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, email, hashed_password, name, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', (admin_id, admin_email, admin_password, 'Administrator', 1))
    
    conn.commit()
    conn.close()

def populate_test_data():
    """Populate test data only in preview environment"""
    env = os.environ.get('RAILWAY_ENVIRONMENT', 'development').lower()
    print(f"🔍 Environment detected: {env}")
    print(f"🔍 Database path: {get_db_path()}")
    
    if env != 'preview':
        print(f"❌ Skipping test data - not in preview environment (env={env})")
        return  # Only populate test data in preview
    
    print("📊 Starting test data population for preview environment...")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
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
    print(f"✅ Test data populated for {env} environment")

init_db()

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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
def get_current_user(authorization: str = None):
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

@app.get("/health")
async def health():
    return {"status": "healthy"}

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
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, hashed_password FROM users WHERE email = ?", (user_data.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(user_data.password, user[1]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create tokens
    access_token = create_token(user[0])
    refresh_token = create_token(user[0])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_endpoint():
    # For demo purposes, return the first user or admin
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, hashed_password, name, timezone, is_active, is_admin, created_at FROM users LIMIT 1")
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse(
        id=user[0],
        email=user[1],
        name=user[3],
        timezone=user[4],
        is_active=bool(user[5]),
        is_admin=bool(user[6]),
        created_at=user[7]
    )

# Family Members endpoints
@app.get("/api/v1/family/members", response_model=List[FamilyMemberResponse])
async def get_family_members():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo - for production, use proper auth)
    cursor.execute("SELECT id, is_admin FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
    is_admin = bool(user[1])
    
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
async def create_family_member(member_data: FamilyMemberCreate):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
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
        SELECT id, email, name, timezone, is_active, is_admin, created_at
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
            'created_at': user[6]
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
async def get_pantry_items():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
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
async def add_pantry_item(pantry_data: PantryItemCreate):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
    
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
async def update_pantry_item(ingredient_id: str, pantry_data: PantryItemUpdate):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
    
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
async def remove_pantry_item(ingredient_id: str):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
    
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
async def get_meal_recommendations(request: MealRecommendationRequest):
    print(f"🎯 RECOMMENDATIONS REQUEST - {datetime.datetime.now()}")
    print(f"📝 Request: {request}")
    logger.info("=== RECOMMENDATIONS REQUEST RECEIVED ===")
    logger.info(f"Request: {request}")
    logger.info(f"Time: {datetime.datetime.now()}")
    logger.info("="*50)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
    
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

if __name__ == "__main__":
    import uvicorn
    # Railway uses PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Food Planning API on port {port}")
    print(f"📊 Health check endpoint: http://0.0.0.0:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")