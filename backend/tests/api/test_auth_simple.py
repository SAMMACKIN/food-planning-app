"""
Simple but comprehensive authentication API tests
"""
import pytest


@pytest.mark.api
class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_admin_login_success(self, client):
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
        # Check that tokens are provided
        assert "refresh_token" in data
        assert "expires_in" in data
    
    def test_admin_login_wrong_password(self, client):
        """Test admin login with wrong password"""
        login_data = {
            "email": "admin",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_user_registration_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Should not return password in response
        user_info = data.get("user", {})
        assert "password" not in user_info
        assert "hashed_password" not in user_info
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "First User"
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        user_data["name"] = "Second User"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/admin/users")
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_protected_endpoint_with_valid_token(self, admin_headers, client):
        """Test accessing protected endpoint with valid admin token"""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        
        # Should be able to access admin endpoint
        assert response.status_code == 200
        # Should return list of users
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1  # At least admin user should exist
    
    def test_token_validation_invalid_token(self, client):
        """Test token validation with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/admin/users", headers=headers)
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_complete_user_workflow(self, client):
        """Test complete user registration → login → protected access workflow"""
        # Step 1: Register new user
        user_data = {
            "email": "workflow@example.com",
            "password": "workflow123",
            "name": "Workflow User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Step 2: Login with same credentials
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]
        
        # Step 3: Try to access admin endpoint (should fail - not admin)
        headers = {"Authorization": f"Bearer {login_token}"}
        admin_response = client.get("/api/v1/admin/users", headers=headers)
        
        assert admin_response.status_code == 403
        assert "Admin access required" in admin_response.json()["detail"]


@pytest.mark.api 
class TestAuthValidation:
    """Test authentication input validation"""
    
    def test_registration_invalid_email(self, client):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_registration_missing_fields(self, client):
        """Test registration with missing required fields"""
        # Missing password
        response1 = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response1.status_code == 422
        
        # Missing email
        response2 = client.post("/api/v1/auth/register", json={
            "password": "password123",
            "name": "Test User"
        })
        assert response2.status_code == 422
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        # Missing password
        response1 = client.post("/api/v1/auth/login", json={"email": "admin"})
        assert response1.status_code == 422
        
        # Missing email
        response2 = client.post("/api/v1/auth/login", json={"password": "admin123"})
        assert response2.status_code == 422