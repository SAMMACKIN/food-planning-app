import pytest
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import init_database, get_db_path


@pytest.fixture(scope="session")
def test_db():
    """Create a temporary test database for modular app"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        # Initialize the database directly without mocking
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create all required tables directly
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
            allergens TEXT,
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
        CREATE TABLE IF NOT EXISTS saved_recipes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            prep_time INTEGER,
            difficulty TEXT,
            servings INTEGER,
            ingredients_needed TEXT,
            instructions TEXT,
            tags TEXT,
            nutrition_notes TEXT,
            pantry_usage_score REAL,
            ai_generated BOOLEAN DEFAULT 0,
            ai_provider TEXT,
            source TEXT,
            times_cooked INTEGER DEFAULT 0,
            last_cooked DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ratings (
            id TEXT PRIMARY KEY,
            recipe_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            would_make_again BOOLEAN,
            cooking_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES saved_recipes (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(recipe_id, user_id)
        )
        ''')
        
        # Create admin user for testing
        import uuid
        from app.core.security import hash_password
        admin_id = str(uuid.uuid4())
        admin_password = hash_password("admin123")
        
        cursor.execute('''
        INSERT OR IGNORE INTO users (id, email, name, hashed_password, is_admin, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, "admin", "Admin User", admin_password, 1, 1))
        
        # Add some basic ingredients for testing
        ingredients = [
            ("ingredient-1", "Chicken Breast", "Protein", "piece", 165, 31, 0, 3.6, ""),
            ("ingredient-2", "Rice", "Grain", "cup", 205, 4, 45, 0.5, ""),
            ("ingredient-3", "Broccoli", "Vegetable", "cup", 25, 3, 5, 0, "")
        ]
        
        for ing_id, name, category, unit, calories, protein, carbs, fat, allergens in ingredients:
            cursor.execute('''
            INSERT OR IGNORE INTO ingredients (id, name, category, unit, calories_per_unit, protein_per_unit, carbs_per_unit, fat_per_unit, allergens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ing_id, name, category, unit, calories, protein, carbs, fat, allergens))
        
        conn.commit()
        conn.close()
        
        yield db_path
        
    finally:
        # Cleanup
        os.close(db_fd)
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create a test client with test database"""
    # Mock the get_db_path function to use test database
    with patch('app.core.database.get_db_path', return_value=test_db):
        yield TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin authentication token"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        pytest.fail(f"Failed to get admin token: {response.status_code} - {response.text}")


@pytest.fixture
def admin_headers(admin_token):
    """Get authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    import uuid
    return {
        "email": f"test-{uuid.uuid4()}@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }


@pytest.fixture
def authenticated_user(client, sample_user_data):
    """Create an authenticated user and return the access token"""
    # Register user
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 200
    
    auth_data = response.json()
    return {
        "access_token": auth_data["access_token"],
        "user_data": sample_user_data
    }


@pytest.fixture
def auth_headers(authenticated_user):
    """Get authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {authenticated_user['access_token']}"}


@pytest.fixture
def mock_claude_api():
    """Mock Claude API responses"""
    with patch('app.services.ai_service.is_ai_available', return_value=True):
        with patch('app.services.ai_service.get_meal_recommendations') as mock_ai:
            mock_ai.return_value = [
                {
                    "name": "Mock AI Recipe",
                    "description": "AI generated test recipe",
                    "prep_time": 30,
                    "difficulty": "Easy",
                    "servings": 4,
                    "ingredients_needed": [
                        {"name": "test ingredient", "amount": "1 cup", "category": "test"}
                    ],
                    "instructions": ["Step 1: Test", "Step 2: Verify"],
                    "tags": ["test", "mock"],
                    "nutrition_notes": "Test nutrition",
                    "pantry_usage_score": 0.8,
                    "ai_generated": True,
                    "ai_provider": "claude"
                }
            ]
            yield mock_ai


@pytest.fixture
def sample_ingredient():
    """Sample ingredient data for testing"""
    return {
        "name": "Test Ingredient",
        "category": "Protein",
        "unit": "piece",
        "calories_per_unit": 100,
        "common_uses": ["cooking", "baking"]
    }


@pytest.fixture
def sample_family_member():
    """Sample family member data for testing"""
    return {
        "name": "Test Family Member",
        "age": 25,
        "dietary_restrictions": ["vegetarian"],
        "preferences": {
            "favorite_cuisines": ["italian"],
            "disliked_ingredients": ["mushrooms"],
            "spice_tolerance": "medium"
        }
    }


# Test data factories
class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create_user_data(email=None, name="Test User", password="testpass123"):
        import uuid
        if email is None:
            email = f"test-{uuid.uuid4()}@example.com"
        return {
            "email": email,
            "name": name,
            "password": password
        }


class IngredientFactory:
    """Factory for creating test ingredients"""
    
    @staticmethod
    def create_ingredient_data(name="Test Ingredient", category="Other"):
        return {
            "name": name,
            "category": category,
            "unit": "piece",
            "calories_per_unit": 100,
            "common_uses": ["cooking"]
        }


class FamilyMemberFactory:
    """Factory for creating test family members"""
    
    @staticmethod
    def create_family_member_data(name="Test Member", age=25):
        return {
            "name": name,
            "age": age,
            "dietary_restrictions": [],
            "preferences": {
                "favorite_cuisines": ["italian"],
                "disliked_ingredients": [],
                "spice_tolerance": "medium"
            }
        }