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

app = FastAPI(title="Food Planning API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('simple_food_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            name TEXT,
            timezone TEXT DEFAULT 'UTC',
            is_active BOOLEAN DEFAULT 1,
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

# Routes
@app.get("/")
async def root():
    return {"message": "Food Planning App API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
async def get_current_user(authorization: str = Depends(lambda: None)):
    # Simple auth check for demo
    conn = sqlite3.connect('simple_food_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
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
        created_at=user[6]
    )

# Family Members endpoints
@app.get("/api/v1/family/members", response_model=List[FamilyMemberResponse])
async def get_family_members():
    conn = sqlite3.connect('simple_food_app.db')
    cursor = conn.cursor()
    
    # Get current user (simplified for demo)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user[0]
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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

# Ingredients endpoints
@app.get("/api/v1/ingredients", response_model=List[IngredientResponse])
async def get_ingredients():
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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
    conn = sqlite3.connect('simple_food_app.db')
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)