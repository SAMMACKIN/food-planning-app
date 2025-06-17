import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.db.database import Base, get_db
from simple_app import app


@pytest.fixture(scope="session")
def test_db():
    """Create a temporary test database"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create engine for test database
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine, db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing"""
    engine, _ = test_db
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_db):
    """Create a test client with a test database"""
    engine, _ = test_db
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_claude_api():
    """Mock Claude API responses"""
    with patch('simple_app.claude_available', True):
        with patch('simple_app.get_claude_recommendations') as mock_claude:
            mock_claude.return_value = [
                {
                    "name": "Mock AI Recipe",
                    "description": "AI generated test recipe",
                    "prep_time": 30,
                    "difficulty": "Easy",
                    "servings": 4,
                    "ingredients_needed": [
                        {"name": "Test Ingredient", "quantity": "1", "unit": "cup", "have_in_pantry": True}
                    ],
                    "instructions": ["Step 1: Test instruction"],
                    "tags": ["AI-Generated", "test"],
                    "nutrition_notes": "Test nutrition info",
                    "pantry_usage_score": 90,
                    "ai_generated": True
                }
            ]
            yield mock_claude


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
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
def sample_meal():
    """Sample meal data for testing"""
    return {
        "name": "Test Meal",
        "description": "A test meal",
        "prep_time": 30,
        "difficulty": "Easy",
        "servings": 4,
        "meal_type": "dinner",
        "instructions": ["Step 1", "Step 2"],
        "tags": ["test", "healthy"]
    }


# Test data factories
class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create_user_data(email="test@example.com", name="Test User", password="testpass123"):
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


class MealFactory:
    """Factory for creating test meals"""
    
    @staticmethod
    def create_meal_data(name="Test Meal", meal_type="dinner"):
        return {
            "name": name,
            "description": f"A test {meal_type} meal",
            "prep_time": 30,
            "difficulty": "Easy",
            "servings": 4,
            "meal_type": meal_type,
            "instructions": ["Step 1", "Step 2"],
            "tags": ["test", "healthy"]
        }