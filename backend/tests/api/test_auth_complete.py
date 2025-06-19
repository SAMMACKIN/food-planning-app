"""
Comprehensive authentication API tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import jwt
from datetime import datetime, timedelta

# Import the FastAPI app
from simple_app import app, JWT_SECRET, JWT_ALGORITHM

client = TestClient(app)


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["name"] == user_data["name"]
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com", 
            "password": "password123",
            "name": "User One"
        }
        
        # Register first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register same email again
        user_data["name"] = "User Two"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_user_registration_invalid_email(self):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "password123", 
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_user_registration_weak_password(self):
        """Test registration with weak password"""
        user_data = {
            "email": "weakpass@example.com",
            "password": "123",  # Too short
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality"""
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        login_data = {
            "email": "admin",
            "password": "admin123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "admin"
        assert data["user"]["is_admin"] is True
    
    def test_admin_login_invalid_credentials(self):
        """Test admin login with wrong password"""
        login_data = {
            "email": "admin",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        # Missing password
        response1 = client.post("/api/v1/auth/login", json={"email": "admin"})
        assert response1.status_code == 422
        
        # Missing email
        response2 = client.post("/api/v1/auth/login", json={"password": "admin123"})
        assert response2.status_code == 422


class TestTokenValidation:
    """Test JWT token validation"""
    
    def test_token_validation_valid(self):
        """Test validation of valid token"""
        # Login to get a valid token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/admin/analytics", headers=headers)
        
        # Should not get 401 Unauthorized
        assert response.status_code != 401
    
    def test_token_validation_invalid(self):
        """Test validation of invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/admin/analytics", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_token_validation_expired(self):
        """Test validation of expired token"""
        # Create an expired token
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/admin/analytics", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_token_validation_missing_authorization(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/admin/analytics")
        
        assert response.status_code == 401
        assert "Missing authorization header" in response.json()["detail"]
    
    def test_token_validation_malformed_header(self):
        """Test malformed authorization header"""
        # Missing "Bearer " prefix
        headers = {"Authorization": "invalid_format_token"}
        response = client.get("/api/v1/admin/analytics", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authorization header" in response.json()["detail"]


class TestUserAuthentication:
    """Test user authentication workflow"""
    
    def test_complete_auth_workflow(self):
        """Test complete registration -> login -> protected access workflow"""
        # Step 1: Register new user
        user_data = {
            "email": "workflow@example.com",
            "password": "workflow123",
            "name": "Workflow User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        register_token = register_response.json()["access_token"]
        
        # Step 2: Login with same credentials
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]
        
        # Step 3: Access user endpoints with token
        headers = {"Authorization": f"Bearer {login_token}"}
        profile_response = client.get("/api/v1/users/me", headers=headers)
        
        # Should be able to access user profile
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]
        assert profile_data["name"] == user_data["name"]
    
    def test_user_cannot_access_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints"""
        # Register and login as regular user
        user_data = {
            "email": "regular@example.com",
            "password": "regular123",
            "name": "Regular User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Try to access admin endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/admin/analytics", headers=headers)
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]


class TestPasswordSecurity:
    """Test password security in authentication"""
    
    def test_password_not_returned_in_responses(self):
        """Test that passwords are never returned in API responses"""
        # Register user
        user_data = {
            "email": "security@example.com",
            "password": "securepass123",
            "name": "Security User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        register_data = register_response.json()
        
        # Password should not be in registration response
        assert "password" not in register_data.get("user", {})
        assert "hashed_password" not in register_data.get("user", {})
        
        # Login and check response
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        login_data = login_response.json()
        
        # Password should not be in login response
        assert "password" not in login_data.get("user", {})
        assert "hashed_password" not in login_data.get("user", {})
        
        # Get user profile and check response
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.get("/api/v1/users/me", headers=headers)
        profile_data = profile_response.json()
        
        # Password should not be in profile response
        assert "password" not in profile_data
        assert "hashed_password" not in profile_data