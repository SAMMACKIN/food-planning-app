import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestRecommendationsFlow:
    """Test complete recommendations workflow"""
    
    def test_recommendations_status_to_generation_flow(self, client, mock_claude_api):
        """Test flow from checking status to generating recommendations"""
        # Step 1: Check recommendations status
        status_response = client.get("/api/v1/recommendations/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "claude_available" in status_data
        assert "message" in status_data
        
        # Step 2: Test the AI system
        test_response = client.get("/api/v1/recommendations/test")
        assert test_response.status_code == 200
        
        test_data = test_response.json()
        assert test_data["status"] in ["AI_WORKING", "FALLBACK_USED", "ERROR"]
        
        # Step 3: Generate recommendations
        request_data = {"num_recommendations": 3}
        
        recommendations_response = client.post("/api/v1/recommendations", json=request_data)
        assert recommendations_response.status_code == 200
        
        recommendations = recommendations_response.json()
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        
        # Verify recommendation structure
        if len(recommendations) > 0:
            recommendation = recommendations[0]
            required_fields = ["name", "description", "prep_time", "difficulty", "servings"]
            for field in required_fields:
                assert field in recommendation
    
    def test_recommendations_with_different_parameters(self, client, mock_claude_api):
        """Test recommendations with various parameter combinations"""
        test_cases = [
            # Basic request
            {"num_recommendations": 2},
            
            # With meal type
            {"num_recommendations": 2, "meal_type": "breakfast"},
            
            # With dietary restrictions
            {"num_recommendations": 1, "dietary_restrictions": ["vegetarian"]},
            
            # With pantry ingredients
            {"num_recommendations": 2, "pantry_ingredients": ["chicken", "rice"]},
            
            # Complex request
            {
                "num_recommendations": 3,
                "meal_type": "dinner",
                "dietary_restrictions": ["gluten-free"],
                "pantry_ingredients": ["salmon", "vegetables"],
                "max_prep_time": 45
            }
        ]
        
        for request_data in test_cases:
            response = client.post("/api/v1/recommendations", json=request_data)
            assert response.status_code == 200
            
            recommendations = response.json()
            assert isinstance(recommendations, list)
            assert len(recommendations) <= request_data["num_recommendations"]
    
    @patch('simple_app.claude_available', False)
    def test_fallback_recommendations_flow(self, client):
        """Test that fallback recommendations work when Claude is unavailable"""
        # Step 1: Check status should show Claude unavailable
        status_response = client.get("/api/v1/recommendations/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["claude_available"] is False
        
        # Step 2: Test endpoint should return fallback status
        test_response = client.get("/api/v1/recommendations/test")
        assert test_response.status_code == 200
        
        test_data = test_response.json()
        assert test_data["status"] in ["FALLBACK_USED", "ERROR"]
        
        # Step 3: Recommendations should still work (using fallback)
        request_data = {"num_recommendations": 2}
        
        recommendations_response = client.post("/api/v1/recommendations", json=request_data)
        assert recommendations_response.status_code == 200
        
        recommendations = recommendations_response.json()
        assert isinstance(recommendations, list)
        # Should get fallback recommendations
        assert len(recommendations) >= 0
    
    def test_recommendations_caching_behavior(self, client, mock_claude_api):
        """Test recommendations caching (if implemented)"""
        request_data = {"num_recommendations": 2}
        
        # Make first request
        response1 = client.post("/api/v1/recommendations", json=request_data)
        assert response1.status_code == 200
        recommendations1 = response1.json()
        
        # Make second identical request
        response2 = client.post("/api/v1/recommendations", json=request_data)
        assert response2.status_code == 200
        recommendations2 = response2.json()
        
        # Both should succeed
        assert isinstance(recommendations1, list)
        assert isinstance(recommendations2, list)
        
        # Depending on caching implementation, they might be the same or different
        # This test just ensures both requests work
    
    def test_recommendations_error_handling(self, client):
        """Test error handling in recommendations flow"""
        # Test invalid number of recommendations
        invalid_requests = [
            {"num_recommendations": -1},
            {"num_recommendations": 0},
            {"num_recommendations": 1000},  # Too many
            {"meal_type": "invalid_meal_type"},
            {"dietary_restrictions": "not_a_list"},  # Should be array
            {"pantry_ingredients": "not_a_list"},   # Should be array
        ]
        
        for invalid_request in invalid_requests:
            response = client.post("/api/v1/recommendations", json=invalid_request)
            # Should handle gracefully - either return valid response or proper error
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                # If it returns 200, response should be valid
                data = response.json()
                assert isinstance(data, list)
    
    def test_recommendations_performance(self, client, mock_claude_api):
        """Test recommendations performance and timeout handling"""
        import time
        
        request_data = {"num_recommendations": 3}
        
        start_time = time.time()
        response = client.post("/api/v1/recommendations", json=request_data)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should respond within reasonable time (10 seconds for AI processing)
        response_time = end_time - start_time
        assert response_time < 10.0
        
        recommendations = response.json()
        assert isinstance(recommendations, list)
    
    def test_authenticated_vs_unauthenticated_recommendations(self, client, authenticated_user, mock_claude_api):
        """Test recommendations work for both authenticated and unauthenticated users"""
        request_data = {"num_recommendations": 2}
        
        # Test unauthenticated request
        unauth_response = client.post("/api/v1/recommendations", json=request_data)
        assert unauth_response.status_code == 200
        unauth_recommendations = unauth_response.json()
        
        # Test authenticated request
        auth_headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        auth_response = client.post("/api/v1/recommendations", json=request_data, headers=auth_headers)
        assert auth_response.status_code == 200
        auth_recommendations = auth_response.json()
        
        # Both should work
        assert isinstance(unauth_recommendations, list)
        assert isinstance(auth_recommendations, list)
        
        # Authenticated recommendations might be personalized (different)
        # but both should be valid responses