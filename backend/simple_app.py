import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import sqlite3
import hashlib
import jwt
import uvicorn
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

app = FastAPI(
    title="Food Planning App API",
    description="AI-powered meal planning and pantry management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Database setup
DATABASE_PATH = "simple_food_app.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with required tables"""
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                name TEXT,
                timezone TEXT DEFAULT 'UTC',
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ingredients table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                calories_per_unit REAL DEFAULT 0,
                protein_per_unit REAL DEFAULT 0,
                carbs_per_unit REAL DEFAULT 0,
                fat_per_unit REAL DEFAULT 0,
                allergens TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Pantry items table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pantry_items (
                user_id TEXT,
                ingredient_id TEXT,
                quantity REAL NOT NULL,
                expiration_date DATE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, ingredient_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            )
        """)
        
        # Family members table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                dietary_restrictions TEXT DEFAULT '[]',
                preferences TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Meal plans table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date DATE NOT NULL,
                meal_type TEXT NOT NULL,
                meal_name TEXT NOT NULL,
                meal_description TEXT,
                recipe_data TEXT,
                ai_generated BOOLEAN DEFAULT 0,
                ai_provider TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Meal reviews table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meal_reviews (
                id TEXT PRIMARY KEY,
                meal_plan_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                review_text TEXT,
                would_make_again BOOLEAN DEFAULT 1,
                preparation_notes TEXT,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        
        # Insert sample ingredients if table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM ingredients")
        if cursor.fetchone()[0] == 0:
            sample_ingredients = [
                ("ing_1", "Chicken Breast", "Meat", "pound", 231, 43.5, 0, 5),
                ("ing_2", "Rice", "Grain", "cup", 205, 4.3, 45, 0.4),
                ("ing_3", "Broccoli", "Vegetable", "cup", 25, 3, 5, 0.3),
                ("ing_4", "Olive Oil", "Oil", "tablespoon", 119, 0, 0, 13.5),
                ("ing_5", "Onion", "Vegetable", "medium", 44, 1.2, 10.3, 0.1),
                ("ing_6", "Garlic", "Vegetable", "clove", 4, 0.2, 1, 0),
                ("ing_7", "Tomato", "Vegetable", "medium", 22, 1.1, 4.8, 0.2),
                ("ing_8", "Pasta", "Grain", "cup", 220, 8, 44, 1.1),
                ("ing_9", "Ground Beef", "Meat", "pound", 332, 30, 0, 23),
                ("ing_10", "Cheese", "Dairy", "cup", 113, 7, 1, 9),
                ("ing_11", "Milk", "Dairy", "cup", 149, 8, 12, 8),
                ("ing_12", "Eggs", "Protein", "large", 70, 6, 0.6, 5),
                ("ing_13", "Bread", "Grain", "slice", 79, 2.7, 13, 1.2),
                ("ing_14", "Butter", "Dairy", "tablespoon", 102, 0.1, 0, 11.5),
                ("ing_15", "Salmon", "Fish", "fillet", 206, 22, 0, 12),
                ("ing_16", "Spinach", "Vegetable", "cup", 7, 0.9, 1.1, 0.1),
                ("ing_17", "Bell Pepper", "Vegetable", "medium", 24, 1, 5.5, 0.2),
                ("ing_18", "Mushrooms", "Vegetable", "cup", 15, 2.2, 2.3, 0.2),
                ("ing_19", "Carrots", "Vegetable", "medium", 25, 0.5, 6, 0.1),
                ("ing_20", "Potatoes", "Vegetable", "medium", 161, 4.3, 37, 0.2)
            ]
            
            for ing in sample_ingredients:
                conn.execute("""
                    INSERT INTO ingredients (id, name, category, unit, calories_per_unit, protein_per_unit, carbs_per_unit, fat_per_unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ing)
            
            conn.commit()
            logger.info("Sample ingredients inserted")

# Pydantic models
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
    expires_in: int = 3600

class FamilyMemberCreate(BaseModel):
    name: str
    age: Optional[int] = None
    dietary_restrictions: Optional[List[str]] = []
    preferences: Optional[Dict[str, Any]] = {}

class PantryItemCreate(BaseModel):
    ingredient_id: str
    quantity: float
    expiration_date: Optional[str] = None

class MealPlanCreate(BaseModel):
    date: str
    meal_type: str
    meal_name: str
    meal_description: Optional[str] = None
    recipe_data: Optional[Dict[str, Any]] = None
    ai_generated: Optional[bool] = False
    ai_provider: Optional[str] = None

class MealReviewCreate(BaseModel):
    rating: int
    review_text: Optional[str] = None
    would_make_again: bool = True
    preparation_notes: Optional[str] = None

class RecommendationRequest(BaseModel):
    num_recommendations: Optional[int] = 5
    meal_type: Optional[str] = None
    ai_provider: Optional[str] = "claude"

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow().timestamp() + 3600}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return dict(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Routes
@app.get("/")
async def root():
    return {"message": "Food Planning App API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    import uuid
    
    with get_db() as conn:
        # Check if user exists
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        
        conn.execute("""
            INSERT INTO users (id, email, hashed_password, name)
            VALUES (?, ?, ?, ?)
        """, (user_id, user_data.email, hashed_password, user_data.name))
        conn.commit()
        
        # Create token
        access_token = create_access_token(user_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=access_token,  # Simplified for demo
            expires_in=3600
        )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE email = ?", (user_data.email,))
        user = cursor.fetchone()
        
        if not user or not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token = create_access_token(user["id"])
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=access_token,  # Simplified for demo
            expires_in=3600
        )

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "timezone": current_user["timezone"],
        "is_active": bool(current_user["is_active"]),
        "is_admin": bool(current_user["is_admin"]),
        "created_at": current_user["created_at"]
    }

@app.get("/api/v1/ingredients")
async def get_ingredients():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM ingredients ORDER BY category, name")
        ingredients = []
        for row in cursor.fetchall():
            ingredients.append({
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "unit": row["unit"],
                "calories_per_unit": row["calories_per_unit"],
                "protein_per_unit": row["protein_per_unit"],
                "carbs_per_unit": row["carbs_per_unit"],
                "fat_per_unit": row["fat_per_unit"],
                "allergens": json.loads(row["allergens"]) if row["allergens"] else [],
                "created_at": row["created_at"]
            })
        return ingredients

@app.get("/api/v1/ingredients/search")
async def search_ingredients(q: str):
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM ingredients 
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY category, name
        """, (f"%{q}%", f"%{q}%"))
        
        ingredients = []
        for row in cursor.fetchall():
            ingredients.append({
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "unit": row["unit"],
                "calories_per_unit": row["calories_per_unit"],
                "protein_per_unit": row["protein_per_unit"],
                "carbs_per_unit": row["carbs_per_unit"],
                "fat_per_unit": row["fat_per_unit"],
                "allergens": json.loads(row["allergens"]) if row["allergens"] else []
            })
        return ingredients

@app.get("/api/v1/pantry")
async def get_pantry(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT p.*, i.name, i.category, i.unit, i.allergens
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.user_id = ?
            ORDER BY i.category, i.name
        """, (current_user["id"],))
        
        pantry_items = []
        for row in cursor.fetchall():
            pantry_items.append({
                "user_id": row["user_id"],
                "ingredient_id": row["ingredient_id"],
                "quantity": row["quantity"],
                "expiration_date": row["expiration_date"],
                "updated_at": row["updated_at"],
                "ingredient": {
                    "id": row["ingredient_id"],
                    "name": row["name"],
                    "category": row["category"],
                    "unit": row["unit"],
                    "allergens": json.loads(row["allergens"]) if row["allergens"] else []
                }
            })
        return pantry_items

@app.post("/api/v1/pantry")
async def add_pantry_item(item: PantryItemCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO pantry_items (user_id, ingredient_id, quantity, expiration_date)
            VALUES (?, ?, ?, ?)
        """, (current_user["id"], item.ingredient_id, item.quantity, item.expiration_date))
        conn.commit()
        return {"message": "Pantry item added successfully"}

@app.put("/api/v1/pantry/{ingredient_id}")
async def update_pantry_item(ingredient_id: str, item: PantryItemCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("""
            UPDATE pantry_items 
            SET quantity = ?, expiration_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND ingredient_id = ?
        """, (item.quantity, item.expiration_date, current_user["id"], ingredient_id))
        conn.commit()
        return {"message": "Pantry item updated successfully"}

@app.delete("/api/v1/pantry/{ingredient_id}")
async def delete_pantry_item(ingredient_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM pantry_items WHERE user_id = ? AND ingredient_id = ?", 
                    (current_user["id"], ingredient_id))
        conn.commit()
        return {"message": "Pantry item removed successfully"}

@app.get("/api/v1/family/members")
async def get_family_members(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM family_members WHERE user_id = ?", (current_user["id"],))
        members = []
        for row in cursor.fetchall():
            members.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "name": row["name"],
                "age": row["age"],
                "dietary_restrictions": json.loads(row["dietary_restrictions"]) if row["dietary_restrictions"] else [],
                "preferences": json.loads(row["preferences"]) if row["preferences"] else {},
                "created_at": row["created_at"]
            })
        return members

@app.post("/api/v1/family/members")
async def add_family_member(member: FamilyMemberCreate, current_user: dict = Depends(get_current_user)):
    import uuid
    
    with get_db() as conn:
        member_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO family_members (id, user_id, name, age, dietary_restrictions, preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (member_id, current_user["id"], member.name, member.age, 
              json.dumps(member.dietary_restrictions), json.dumps(member.preferences)))
        conn.commit()
        return {"message": "Family member added successfully", "id": member_id}

@app.put("/api/v1/family/members/{member_id}")
async def update_family_member(member_id: str, member: FamilyMemberCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("""
            UPDATE family_members 
            SET name = ?, age = ?, dietary_restrictions = ?, preferences = ?
            WHERE id = ? AND user_id = ?
        """, (member.name, member.age, json.dumps(member.dietary_restrictions), 
              json.dumps(member.preferences), member_id, current_user["id"]))
        conn.commit()
        return {"message": "Family member updated successfully"}

@app.delete("/api/v1/family/members/{member_id}")
async def delete_family_member(member_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM family_members WHERE id = ? AND user_id = ?", 
                    (member_id, current_user["id"]))
        conn.commit()
        return {"message": "Family member removed successfully"}

@app.get("/api/v1/recommendations/status")
async def get_recommendations_status():
    return {
        "available_providers": ["fallback"],
        "default_provider": "fallback",
        "message": "Using fallback recommendations (AI providers not configured)"
    }

@app.post("/api/v1/recommendations")
async def get_recommendations(request: RecommendationRequest, current_user: dict = Depends(get_current_user)):
    # Fallback recommendations since AI providers aren't configured
    fallback_recommendations = [
        {
            "name": "Simple Pasta with Garlic",
            "description": "Quick and easy pasta dish with garlic and olive oil",
            "prep_time": 20,
            "difficulty": "Easy",
            "servings": 4,
            "ingredients_needed": [
                {"name": "Pasta", "quantity": "1", "unit": "cup", "have_in_pantry": True},
                {"name": "Garlic", "quantity": "3", "unit": "cloves", "have_in_pantry": True},
                {"name": "Olive Oil", "quantity": "2", "unit": "tablespoons", "have_in_pantry": True}
            ],
            "instructions": [
                "Boil water and cook pasta according to package directions",
                "Heat olive oil in a pan and sauté minced garlic",
                "Toss cooked pasta with garlic oil",
                "Season with salt and pepper to taste"
            ],
            "tags": ["Quick", "Easy", "Vegetarian"],
            "nutrition_notes": "Good source of carbohydrates and healthy fats",
            "pantry_usage_score": 90,
            "ai_generated": False,
            "ai_provider": "fallback"
        },
        {
            "name": "Chicken and Rice Bowl",
            "description": "Protein-rich bowl with seasoned chicken and rice",
            "prep_time": 30,
            "difficulty": "Medium",
            "servings": 4,
            "ingredients_needed": [
                {"name": "Chicken Breast", "quantity": "1", "unit": "pound", "have_in_pantry": True},
                {"name": "Rice", "quantity": "1", "unit": "cup", "have_in_pantry": True},
                {"name": "Onion", "quantity": "1", "unit": "medium", "have_in_pantry": True}
            ],
            "instructions": [
                "Cook rice according to package directions",
                "Season and cook chicken breast until done",
                "Sauté onions until golden",
                "Serve chicken over rice with onions"
            ],
            "tags": ["Protein", "Balanced", "Filling"],
            "nutrition_notes": "High protein meal with complex carbohydrates",
            "pantry_usage_score": 85,
            "ai_generated": False,
            "ai_provider": "fallback"
        },
        {
            "name": "Vegetable Stir Fry",
            "description": "Colorful mix of fresh vegetables stir-fried to perfection",
            "prep_time": 15,
            "difficulty": "Easy",
            "servings": 3,
            "ingredients_needed": [
                {"name": "Broccoli", "quantity": "2", "unit": "cups", "have_in_pantry": True},
                {"name": "Bell Pepper", "quantity": "1", "unit": "medium", "have_in_pantry": True},
                {"name": "Carrots", "quantity": "2", "unit": "medium", "have_in_pantry": True}
            ],
            "instructions": [
                "Heat oil in a large pan or wok",
                "Add harder vegetables first (carrots, broccoli)",
                "Add softer vegetables (bell peppers) later",
                "Stir-fry until vegetables are tender-crisp"
            ],
            "tags": ["Vegetarian", "Healthy", "Quick"],
            "nutrition_notes": "Rich in vitamins, minerals, and fiber",
            "pantry_usage_score": 80,
            "ai_generated": False,
            "ai_provider": "fallback"
        }
    ]
    
    return fallback_recommendations[:request.num_recommendations]

@app.get("/api/v1/meal-plans")
async def get_meal_plans(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM meal_plans 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date, meal_type
        """, (current_user["id"], start_date, end_date))
        
        meal_plans = []
        for row in cursor.fetchall():
            meal_plans.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "date": row["date"],
                "meal_type": row["meal_type"],
                "meal_name": row["meal_name"],
                "meal_description": row["meal_description"],
                "recipe_data": json.loads(row["recipe_data"]) if row["recipe_data"] else None,
                "ai_generated": bool(row["ai_generated"]),
                "ai_provider": row["ai_provider"],
                "created_at": row["created_at"]
            })
        return meal_plans

@app.post("/api/v1/meal-plans")
async def create_meal_plan(meal_plan: MealPlanCreate, current_user: dict = Depends(get_current_user)):
    import uuid
    
    with get_db() as conn:
        plan_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO meal_plans (id, user_id, date, meal_type, meal_name, meal_description, recipe_data, ai_generated, ai_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (plan_id, current_user["id"], meal_plan.date, meal_plan.meal_type, 
              meal_plan.meal_name, meal_plan.meal_description, 
              json.dumps(meal_plan.recipe_data) if meal_plan.recipe_data else None,
              meal_plan.ai_generated, meal_plan.ai_provider))
        conn.commit()
        
        # Return the created meal plan
        cursor = conn.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "date": row["date"],
            "meal_type": row["meal_type"],
            "meal_name": row["meal_name"],
            "meal_description": row["meal_description"],
            "recipe_data": json.loads(row["recipe_data"]) if row["recipe_data"] else None,
            "ai_generated": bool(row["ai_generated"]),
            "ai_provider": row["ai_provider"],
            "created_at": row["created_at"]
        }

@app.delete("/api/v1/meal-plans/{plan_id}")
async def delete_meal_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM meal_plans WHERE id = ? AND user_id = ?", 
                    (plan_id, current_user["id"]))
        conn.commit()
        return {"message": "Meal plan deleted successfully"}

@app.get("/api/v1/meal-plans/{plan_id}/reviews")
async def get_meal_reviews(plan_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM meal_reviews 
            WHERE meal_plan_id = ? AND user_id = ?
            ORDER BY reviewed_at DESC
        """, (plan_id, current_user["id"]))
        
        reviews = []
        for row in cursor.fetchall():
            reviews.append({
                "id": row["id"],
                "meal_plan_id": row["meal_plan_id"],
                "user_id": row["user_id"],
                "rating": row["rating"],
                "review_text": row["review_text"],
                "would_make_again": bool(row["would_make_again"]),
                "preparation_notes": row["preparation_notes"],
                "reviewed_at": row["reviewed_at"]
            })
        return reviews

@app.post("/api/v1/meal-plans/{plan_id}/reviews")
async def create_meal_review(plan_id: str, review: MealReviewCreate, current_user: dict = Depends(get_current_user)):
    import uuid
    
    with get_db() as conn:
        review_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO meal_reviews (id, meal_plan_id, user_id, rating, review_text, would_make_again, preparation_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (review_id, plan_id, current_user["id"], review.rating, 
              review.review_text, review.would_make_again, review.preparation_notes))
        conn.commit()
        
        # Return the created review
        cursor = conn.execute("SELECT * FROM meal_reviews WHERE id = ?", (review_id,))
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "meal_plan_id": row["meal_plan_id"],
            "user_id": row["user_id"],
            "rating": row["rating"],
            "review_text": row["review_text"],
            "would_make_again": bool(row["would_make_again"]),
            "preparation_notes": row["preparation_notes"],
            "reviewed_at": row["reviewed_at"]
        }

# Admin endpoints (simplified)
@app.get("/api/v1/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row["id"],
                "email": row["email"],
                "name": row["name"],
                "timezone": row["timezone"],
                "is_active": bool(row["is_active"]),
                "is_admin": bool(row["is_admin"]),
                "created_at": row["created_at"]
            })
        return users

@app.get("/api/v1/admin/family/all")
async def get_all_family_members(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT f.*, u.email as user_email, u.name as user_name
            FROM family_members f
            JOIN users u ON f.user_id = u.id
            ORDER BY f.created_at DESC
        """)
        
        members = []
        for row in cursor.fetchall():
            members.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "name": row["name"],
                "age": row["age"],
                "dietary_restrictions": json.loads(row["dietary_restrictions"]) if row["dietary_restrictions"] else [],
                "preferences": json.loads(row["preferences"]) if row["preferences"] else {},
                "created_at": row["created_at"],
                "user_email": row["user_email"],
                "user_name": row["user_name"]
            })
        return members

@app.get("/api/v1/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    with get_db() as conn:
        # Get total users
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Get total family members
        cursor = conn.execute("SELECT COUNT(*) FROM family_members")
        total_family_members = cursor.fetchone()[0]
        
        # Get total pantry items
        cursor = conn.execute("SELECT COUNT(*) FROM pantry_items")
        total_pantry_items = cursor.fetchone()[0]
        
        # Get recent registrations (last 30 days)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= datetime('now', '-30 days')
        """)
        recent_registrations = cursor.fetchone()[0]
        
        return {
            "total_users": total_users,
            "total_family_members": total_family_members,
            "total_pantry_items": total_pantry_items,
            "recent_registrations": recent_registrations
        }

if __name__ == "__main__":
    # Initialize database
    init_database()
    logger.info("Database initialized")
    
    # Start server
    port = int(os.environ.get("PORT", 8001))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )