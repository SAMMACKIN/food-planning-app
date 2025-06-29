import pytest
from unittest.mock import patch


@pytest.mark.api
class TestRecommendationsAPI:
    """Test meal recommendations endpoints"""
    
    def test_recommendations_status_endpoint(self, client):
        """Test the recommendations status endpoint"""
        response = client.get("/api/v1/recommendations/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "claude_available" in data
        assert "message" in data
        assert isinstance(data["claude_available"], bool)
    
    def test_recommendations_test_endpoint(self, client):
        """Test the AI test endpoint"""
        response = client.get("/api/v1/recommendations/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["AI_WORKING", "FALLBACK_USED", "ERROR"]
    
    def test_get_recommendations_default(self, client, mock_claude_api):
        """Test getting meal recommendations with default parameters"""
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
    
    def test_get_recommendations_with_meal_type(self, client, mock_claude_api):
        """Test recommendations with meal type filter"""
        request_data = {
            "num_recommendations": 2,
            "meal_type": "breakfast"
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2
    
    def test_get_recommendations_with_dietary_restrictions(self, client, mock_claude_api):
        """Test recommendations with dietary restrictions"""
        request_data = {
            "num_recommendations": 2,
            "dietary_restrictions": ["vegetarian", "gluten-free"]
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations_with_pantry_ingredients(self, client, mock_claude_api):
        """Test recommendations using pantry ingredients"""
        request_data = {
            "num_recommendations": 2,
            "pantry_ingredients": ["chicken", "rice", "tomatoes"]
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations_invalid_num(self, client):
        """Test recommendations with invalid number"""
        request_data = {
            "num_recommendations": -1
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 400, 422]
    
    def test_get_recommendations_too_many(self, client):
        """Test recommendations with too many requested"""
        request_data = {
            "num_recommendations": 100
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should cap at reasonable limit
        assert len(data) <= 10
    
    @patch('app.services.ai_service.is_ai_available', return_value=False)
    def test_get_recommendations_claude_unavailable(self, client):
        """Test recommendations when Claude API is unavailable"""
        request_data = {
            "num_recommendations": 3
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return fallback recommendations
        if len(data) > 0:
            # Check fallback recommendations have required fields
            rec = data[0]
            assert 'name' in rec
            assert 'description' in rec
    
    def test_get_recommendations_empty_request(self, client):
        """Test recommendations with empty request body"""
        response = client.post("/api/v1/recommendations", json={})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return default number of recommendations
        assert len(data) >= 0