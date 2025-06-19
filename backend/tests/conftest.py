import pytest
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

import simple_app


@pytest.fixture(scope="session")
def test_db():
    """Create a temporary test database for simple_app"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Initialize the database with the schema from simple_app
    conn = sqlite3.connect(db_path)
    
    # Create the tables and admin user
    simple_app.init_database_with_connection(conn)
    
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create a test client with test database"""
    # Mock the get_db_path function to use test database
    with patch.object(simple_app, 'get_db_path', return_value=test_db):
        yield TestClient(simple_app.app)


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
            yield mock_claude


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