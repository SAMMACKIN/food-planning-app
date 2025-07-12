"""
Tests for AI recommendations functionality
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.recommendations import ai_service


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing"""
    return {
        'id': 'test-user-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'is_admin': False,
        'is_active': True
    }


class TestAIServiceImport:
    """Test AI service import functionality"""
    
    def test_ai_service_imports_successfully(self):
        """Test that ai_service can be imported without errors"""
        from app.api.recommendations import ai_service
        assert ai_service is not None
        
    def test_ai_service_has_required_methods(self):
        """Test that ai_service has all required methods"""
        assert hasattr(ai_service, 'get_available_providers')
        assert hasattr(ai_service, 'is_provider_available')
        assert hasattr(ai_service, 'get_meal_recommendations')
        
    def test_get_available_providers_returns_dict(self):
        """Test that get_available_providers returns a dictionary"""
        providers = ai_service.get_available_providers()
        assert isinstance(providers, dict)
        assert 'claude' in providers
        assert 'groq' in providers
        assert 'perplexity' in providers
        
    def test_is_provider_available_returns_boolean(self):
        """Test that is_provider_available returns boolean"""
        result = ai_service.is_provider_available('claude')
        assert isinstance(result, bool)


class TestRecommendationsEndpoints:
    """Test AI recommendations API endpoints"""
    
    def test_recommendations_status_endpoint(self, client):
        """Test the /recommendations/status endpoint works"""
        response = client.get("/api/v1/recommendations/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        assert "available_providers" in data
        assert "default_provider" in data
        assert "message" in data
        
        # Verify structure
        assert isinstance(data["providers"], dict)
        assert isinstance(data["available_providers"], list)
        
    def test_recommendations_test_endpoint_claude(self, client):
        """Test the /recommendations/test endpoint with Claude"""
        response = client.get("/api/v1/recommendations/test?provider=claude")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "provider" in data
        assert data["provider"] == "claude"
        
        # Should either work, be unavailable, have no results, or error with test keys
        assert data["status"] in ["AI_WORKING", "PROVIDER_UNAVAILABLE", "NO_RESULTS", "ERROR"]
        
    def test_recommendations_test_endpoint_groq(self, client):
        """Test the /recommendations/test endpoint with Groq"""
        response = client.get("/api/v1/recommendations/test?provider=groq")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "provider" in data
        assert data["provider"] == "groq"
        
    def test_recommendations_test_endpoint_perplexity(self, client):
        """Test the /recommendations/test endpoint with Perplexity"""
        response = client.get("/api/v1/recommendations/test?provider=perplexity")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "provider" in data
        assert data["provider"] == "perplexity"
        
    def test_recommendations_test_endpoint_invalid_provider(self, client):
        """Test the /recommendations/test endpoint with invalid provider"""
        response = client.get("/api/v1/recommendations/test?provider=invalid")
        assert response.status_code == 200
        
        data = response.json()
        # Invalid provider should return PROVIDER_UNAVAILABLE, not ERROR
        assert data["status"] == "PROVIDER_UNAVAILABLE"


class TestAIRecommendationsIntegration:
    """Test AI recommendations integration with database and auth"""
    
    @patch('app.api.recommendations.get_current_user')
    def test_recommendations_endpoint_requires_auth(self, mock_auth, client):
        """Test that recommendations endpoint requires authentication"""
        mock_auth.return_value = None
        
        response = client.post("/api/v1/recommendations", json={
            "num_recommendations": 3,
            "ai_provider": "claude"
        })
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
        
    @patch('app.api.recommendations.get_current_user')
    @patch('app.api.recommendations.get_db_connection')
    async def test_recommendations_endpoint_with_valid_auth(self, mock_db, mock_auth, client, mock_auth_user):
        """Test recommendations endpoint with valid authentication"""
        mock_auth.return_value = mock_auth_user
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        
        # Mock empty family and pantry data
        mock_cursor.fetchall.return_value = []
        
        # Mock AI service response
        with patch.object(ai_service, 'get_meal_recommendations') as mock_ai:
            mock_ai.return_value = [{
                "name": "Test Recipe",
                "description": "A test recipe",
                "prep_time": 30,
                "difficulty": "Easy",
                "servings": 2,
                "ingredients_needed": ["test ingredient"],
                "instructions": ["test step"],
                "tags": ["test"],
                "nutrition_notes": "Test nutrition",
                "pantry_usage_score": 50,
                "ai_generated": True,
                "ai_provider": "claude"
            }]
            
            response = client.post("/api/v1/recommendations", 
                json={"num_recommendations": 1, "ai_provider": "claude"},
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Test Recipe"
            assert data[0]["ai_generated"] == True


class TestAIServiceFallback:
    """Test AI service fallback behavior when import fails"""
    
    def test_ai_service_works_when_imported_successfully(self):
        """Test that AI service works when imported successfully"""
        # Since we're testing with the real AI service that imported successfully,
        # just verify it has the expected interface
        assert hasattr(ai_service, 'is_provider_available')
        assert hasattr(ai_service, 'get_available_providers')
        assert hasattr(ai_service, 'get_meal_recommendations')
        
        # Test that at least one provider is available (Claude should be)
        providers = ai_service.get_available_providers()
        assert isinstance(providers, dict)
        # At least Claude should be available based on startup logs
        assert providers.get('claude', False) == True
        
    @pytest.mark.asyncio
    async def test_ai_service_can_generate_recommendations(self):
        """Test that AI service can generate recommendations when working"""
        # Skip if using test API keys (they won't work with real API)
        import os
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        if claude_key.startswith("test-"):
            pytest.skip("Skipping real API test with test credentials")
            
        # Only test if Claude is available
        if ai_service.is_provider_available('claude'):
            recommendations = await ai_service.get_meal_recommendations(
                family_members=[],
                pantry_items=[],
                num_recommendations=1,
                provider='claude'
            )
            
            assert len(recommendations) >= 1
            rec = recommendations[0]
            
            # Verify required fields
            required_fields = [
                "name", "description", "prep_time", "difficulty", "servings",
                "ingredients_needed", "instructions", "tags", "nutrition_notes",
                "pantry_usage_score"
            ]
            
            for field in required_fields:
                assert field in rec
                
            # Should be AI generated when using real service
            assert rec.get("ai_generated", False) == True
            assert rec.get("ai_provider") == "claude"


if __name__ == "__main__":
    pytest.main([__file__])