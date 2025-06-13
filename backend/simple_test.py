#!/usr/bin/env python3
"""
Simple test runner for the Food Planning App backend
"""

from fastapi.testclient import TestClient
from simple_app import app

# Create test client
client = TestClient(app)

def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}
    print("✅ Health endpoint test passed")

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "Food Planning App API"}
    print("✅ Root endpoint test passed")

def test_recommendations_status():
    """Test recommendations status endpoint"""
    response = client.get("/api/v1/recommendations/status")
    assert response.status_code == 200
    data = response.json()
    assert "claude_available" in data
    assert "message" in data
    print("✅ Recommendations status test passed")

def test_recommendations_test_endpoint():
    """Test AI test endpoint"""
    response = client.get("/api/v1/recommendations/test")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["AI_WORKING", "FALLBACK_USED", "ERROR"]
    print(f"✅ AI test endpoint: {data['status']}")

def test_ingredients_list():
    """Test getting ingredients"""
    response = client.get("/api/v1/ingredients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have sample ingredients
    print(f"✅ Ingredients endpoint: {len(data)} ingredients found")

def test_recommendations():
    """Test meal recommendations"""
    request_data = {"num_recommendations": 3}
    response = client.post("/api/v1/recommendations", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    
    if len(data) > 0:
        rec = data[0]
        assert "name" in rec
        assert "ai_generated" in rec
        print(f"✅ Recommendations test: Got {len(data)} recommendations")
        print(f"   First recipe: {rec['name']} (AI: {rec['ai_generated']})")
    else:
        print("⚠️  No recommendations returned")

def run_all_tests():
    """Run all backend tests"""
    print("🧪 Running Backend Tests")
    print("=" * 50)
    
    try:
        test_health_endpoint()
        test_root_endpoint()
        test_recommendations_status()
        test_recommendations_test_endpoint()
        test_ingredients_list()
        test_recommendations()
        
        print("=" * 50)
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)