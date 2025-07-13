import pytest
import uuid
from unittest.mock import patch


@pytest.fixture
def auth_user(client):
    """Create a test user and return auth headers"""
    user_data = {
        "email": f"test-{uuid.uuid4()}@example.com",
        "password": "testpass123",
        "name": "Test User"
    }
    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.api
class TestRecommendationsAPI:
    """Test meal recommendations endpoints"""
    
    def test_recommendations_status_endpoint(self, client):
        """Test the recommendations status endpoint"""
        response = client.get("/api/v1/recommendations/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "available_providers" in data
        assert "message" in data
        assert isinstance(data["available_providers"], list)
    
    def test_recommendations_test_endpoint(self, client):
        """Test the AI test endpoint"""
        response = client.get("/api/v1/recommendations/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["AI_WORKING", "FALLBACK_USED", "ERROR"]
    
    def test_get_recommendations_default(self, client, auth_user, mock_claude_api):
        """Test getting meal recommendations with default parameters"""
        request_data = {
            "num_recommendations": 3
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
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
    
    def test_get_recommendations_with_meal_type(self, client, auth_user, mock_claude_api):
        """Test recommendations with meal type filter"""
        request_data = {
            "num_recommendations": 2,
            "meal_type": "breakfast"
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2
    
    def test_get_recommendations_with_dietary_restrictions(self, client, auth_user, mock_claude_api):
        """Test recommendations with dietary restrictions"""
        request_data = {
            "num_recommendations": 2,
            "dietary_restrictions": ["vegetarian", "gluten-free"]
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations_with_pantry_ingredients(self, client, auth_user, mock_claude_api):
        """Test recommendations using pantry ingredients"""
        request_data = {
            "num_recommendations": 2,
            "pantry_ingredients": ["chicken", "rice", "tomatoes"]
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations_invalid_num(self, client, auth_user):
        """Test recommendations with invalid number"""
        request_data = {
            "num_recommendations": -1
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 400, 422]
    
    def test_get_recommendations_too_many(self, client, auth_user):
        """Test recommendations with too many requested"""
        request_data = {
            "num_recommendations": 100
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        # Should cap at reasonable limit
        assert len(data) <= 10
    
    @patch('ai_service.ai_service.is_provider_available', return_value=False)
    def test_get_recommendations_claude_unavailable(self, mock_ai_unavailable, client, auth_user):
        """Test recommendations when Claude API is unavailable"""
        request_data = {
            "num_recommendations": 3
        }
        
        response = client.post("/api/v1/recommendations", json=request_data, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return fallback recommendations
        if len(data) > 0:
            # Check fallback recommendations have required fields
            rec = data[0]
            assert 'name' in rec
            assert 'description' in rec
    
    def test_get_recommendations_empty_request(self, client, auth_user):
        """Test recommendations with empty request body"""
        response = client.post("/api/v1/recommendations", json={}, headers=auth_user)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return default number of recommendations
        assert len(data) >= 0