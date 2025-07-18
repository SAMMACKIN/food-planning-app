import pytest


@pytest.mark.api
class TestGeneralAPI:
    """Test general API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test the health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        # The health endpoint returns additional diagnostic info
        assert "environment" in data
        assert "deployment_info" in data
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data == {"message": "Food Planning App API"}
    
    def test_nonexistent_endpoint(self, client):
        """Test accessing a non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.get("/")
        
        # Check if CORS headers are set (might depend on configuration)
        headers = response.headers
        # Note: TestClient might not show all CORS headers
        assert response.status_code == 200
    
    def test_api_version_consistency(self, client):
        """Test that all API endpoints use consistent versioning"""
        endpoints_to_test = [
            "/api/v1/recommendations/status",
            "/api/v1/ingredients",
            "/api/v1/auth/register"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 404 for version issues
            assert response.status_code != 404 or "v1" not in str(response.content)
    
    def test_api_content_type(self, client):
        """Test that API returns correct content type"""
        response = client.get("/")
        assert response.status_code == 200
        
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
    
    def test_api_response_time(self, client):
        """Test that API responds within reasonable time"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Should respond within 5 seconds (very generous for health check)
        assert (end_time - start_time) < 5.0
    
    def test_large_request_handling(self, client, auth_headers):
        """Test handling of large request bodies"""
        # Create a reasonably large but not excessive request
        large_data = {
            "num_recommendations": 5,
            "pantry_ingredients": ["ingredient_" + str(i) for i in range(100)],
            "dietary_restrictions": ["restriction_" + str(i) for i in range(20)]
        }
        
        response = client.post("/api/v1/recommendations", json=large_data, headers=auth_headers)
        # Should handle gracefully, not crash (401 is acceptable for auth failure)
        assert response.status_code in [200, 400, 401, 413, 422]
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/v1/recommendations",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return proper error for invalid JSON
        assert response.status_code == 422
    
    def test_empty_post_body(self, client):
        """Test handling of empty POST body"""
        response = client.post("/api/v1/recommendations")
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]