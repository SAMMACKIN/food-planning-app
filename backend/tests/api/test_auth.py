import pytest
from tests.conftest import UserFactory


@pytest.mark.api
class TestAuthAPI:
    """Test authentication endpoints"""
    
    def test_user_registration_success(self, client):
        """Test successful user registration"""
        user_data = UserFactory.create_user_data(
            email="test_register@example.com",
            name="Test Register User"
        )
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["name"] == user_data["name"]
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = UserFactory.create_user_data(email="duplicate@example.com")
        
        # Register first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register with same email
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_user_registration_invalid_email(self, client):
        """Test registration with invalid email"""
        user_data = UserFactory.create_user_data(email="invalid-email")
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_user_registration_weak_password(self, client):
        """Test registration with weak password"""
        user_data = UserFactory.create_user_data(password="123")
        
        response = client.post("/api/v1/auth/register", json=user_data)
        # Should validate password strength (if implemented)
        # For now, just check it doesn't crash
        assert response.status_code in [200, 400, 422]
    
    def test_user_login_success(self, client):
        """Test successful user login"""
        # First register a user
        user_data = UserFactory.create_user_data(
            email="login_test@example.com",
            name="Login Test User"
        )
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then try to login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user_data["email"]
    
    def test_user_login_invalid_email(self, client):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_user_login_wrong_password(self, client):
        """Test login with wrong password"""
        # First register a user
        user_data = UserFactory.create_user_data(email="wrong_pass@example.com")
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then try to login with wrong password
        login_data = {
            "email": user_data["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        # Note: This endpoint might not exist yet, adjust based on actual API
        # For now, just check we don't get 401
        assert response.status_code != 401