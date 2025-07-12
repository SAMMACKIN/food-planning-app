# Set up test environment BEFORE any imports that might load settings
import os
os.environ["TESTING"] = "true"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-testing-only-not-production"

# Use PostgreSQL for tests to match production environment  
# This ensures consistency between local tests, CI, and production
if not os.environ.get("DATABASE_URL"):
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        # CI environment - PostgreSQL service provided by GitHub Actions
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/food_planning_test"
    else:
        # Local development testing - use local PostgreSQL
        os.environ["DATABASE_URL"] = "postgresql://postgres:whbutb2012@localhost:5432/food_planning_test"

os.environ["ENVIRONMENT"] = "test"

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base
from app.core.auth_service import AuthService
from app.models import *  # Import all models to register them

# Test ingredient IDs for consistent testing (using UUID strings for SQL compatibility)
TEST_INGREDIENT_IDS = {
    'chicken_breast': 'df914ffc-6377-405e-a397-d5a0171c3e40',
    'rice': 'a420e989-5c87-42fb-85eb-2117f548845b', 
    'broccoli': 'be300a0f-642d-4578-96e5-62d5afcb0f64'
}


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Test environment is already set up at module level"""
    yield
    # Cleanup is handled by pytest automatically


@pytest.fixture(scope="session")
def test_db():
    """Create and setup PostgreSQL test database"""
    # Use the same DATABASE_URL that was set earlier
    test_db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(test_db_url)
    
    try:
        # Drop all tables if they exist and recreate them
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create session for initial data setup
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Create admin user manually using the test session
            from app.models.user import User
            from app.core.security import hash_password
            import uuid
            
            admin_user = User(
                id=uuid.uuid4(),
                email="admin",
                name="Admin User",
                hashed_password=hash_password("admin123"),
                is_admin=True,
                is_active=True
            )
            session.add(admin_user)
            session.commit()
            
            # Add basic ingredients for testing using proper model schema
            ingredients_sql = text("""
                INSERT INTO ingredients (id, name, category_id, unit, nutritional_info, allergens)
                VALUES 
                    (:id1, 'Chicken Breast', NULL, 'piece', '{"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6}', '[]'),
                    (:id2, 'Rice', NULL, 'cup', '{"calories": 205, "protein": 4, "carbs": 45, "fat": 0.5}', '[]'),
                    (:id3, 'Broccoli', NULL, 'cup', '{"calories": 25, "protein": 3, "carbs": 5, "fat": 0}', '[]')
                ON CONFLICT (id) DO NOTHING
            """)
            
            # Use predictable UUIDs for testing
            session.execute(ingredients_sql, {
                'id1': TEST_INGREDIENT_IDS['chicken_breast'],
                'id2': TEST_INGREDIENT_IDS['rice'],  
                'id3': TEST_INGREDIENT_IDS['broccoli']
            })
            session.commit()
            
        finally:
            session.close()
        
        yield test_db_url
        
    except Exception as e:
        print(f"Test database setup failed: {e}")
        # Try to drop tables even if setup failed
        try:
            Base.metadata.drop_all(bind=engine)
        except:
            pass
        raise
    finally:
        # Cleanup - drop all tables after tests
        try:
            Base.metadata.drop_all(bind=engine)
        except:
            pass
        engine.dispose()


@pytest.fixture
def test_ingredient_ids():
    """Provide consistent ingredient IDs for tests"""
    return TEST_INGREDIENT_IDS


@pytest.fixture
def client(test_db):
    """Create a test client with test database"""
    # Since we're using the same PostgreSQL setup as configured in DATABASE_URL,
    # the application will automatically use the test database
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
    with patch('ai_service.ai_service.is_provider_available', return_value=True):
        with patch('ai_service.ai_service.get_meal_recommendations') as mock_ai:
            mock_ai.return_value = [
                {
                    "name": "Mock AI Recipe",
                    "description": "AI generated test recipe",
                    "prep_time": 30,
                    "difficulty": "Easy",
                    "servings": 4,
                    "ingredients_needed": [
                        "test ingredient 1 cup",
                        "another ingredient 2 tbsp"
                    ],
                    "instructions": ["Step 1: Test", "Step 2: Verify"],
                    "tags": ["test", "mock"],
                    "nutrition_notes": "Test nutrition",
                    "pantry_usage_score": 80,
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
            "likes": ["pasta"],
            "dislikes": ["mushrooms"],
            "preferred_cuisines": ["italian"],
            "spice_level": 2
        }
    }


# Test data factories
class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create_user_data(email=None, name="Test User", password="testpass123"):
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
                "likes": ["pasta"],
                "dislikes": [],
                "preferred_cuisines": ["italian"],
                "spice_level": 2
            }
        }