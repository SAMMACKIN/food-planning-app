import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch
from simple_app import app

# Create test client
client = TestClient(app)


class TestAPI:
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Food Planning App API"}
    
    def test_recommendations_status_endpoint(self):
        """Test the recommendations status endpoint"""
        response = client.get("/api/v1/recommendations/status")
        assert response.status_code == 200
        data = response.json()
        assert "claude_available" in data
        assert "message" in data
    
    def test_recommendations_test_endpoint(self):
        """Test the AI test endpoint"""
        response = client.get("/api/v1/recommendations/test")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["AI_WORKING", "FALLBACK_USED", "ERROR"]
    
    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_user_login(self):
        """Test user login after registration"""
        # First register a user
        user_data = {
            "email": "login_test@example.com", 
            "password": "testpassword123",
            "name": "Login Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then try to login
        login_data = {
            "email": "login_test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_ingredients(self):
        """Test getting ingredients list"""
        response = client.get("/api/v1/ingredients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have sample ingredients
        assert len(data) > 0
        
        # Check first ingredient has required fields
        ingredient = data[0]
        required_fields = ['id', 'name', 'category', 'unit']
        for field in required_fields:
            assert field in ingredient
    
    def test_search_ingredients(self):
        """Test ingredient search"""
        response = client.get("/api/v1/ingredients/search?q=chicken")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should find chicken in results
        chicken_found = any('chicken' in item['name'].lower() for item in data)
        assert chicken_found
    
    def test_get_recommendations(self):
        """Test getting meal recommendations"""
        request_data = {
            "num_recommendations": 3
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3
        
        if len(data) > 0:
            rec = data[0]
            required_fields = ['name', 'description', 'prep_time', 'difficulty', 'servings']
            for field in required_fields:
                assert field in rec
            
            # Check if AI generated flag exists
            assert 'ai_generated' in rec
    
    def test_recommendations_with_meal_type(self):
        """Test recommendations with meal type filter"""
        request_data = {
            "num_recommendations": 2,
            "meal_type": "breakfast"
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__])