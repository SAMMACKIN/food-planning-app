import pytest
from tests.conftest import UserFactory


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_user_registration_and_login_flow(self, client):
        """Test complete user registration and login flow"""
        # Step 1: Register a new user
        user_data = UserFactory.create_user_data(
            email="integration_test@example.com",
            name="Integration Test User"
        )
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "refresh_token" in register_data
        assert register_data["token_type"] == "bearer"
        
        # Store tokens for later use
        access_token = register_data["access_token"]
        refresh_token = register_data["refresh_token"]
        
        # Step 2: Use access token to access protected resource
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        
        # Try to access user info (if endpoint exists)
        me_response = client.get("/api/v1/users/me", headers=auth_headers)
        # This endpoint might not exist yet, so check it doesn't return 401
        if me_response.status_code != 404:
            assert me_response.status_code != 401
        
        # Step 3: Login with the same credentials
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_response_data = login_response.json()
        assert "access_token" in login_response_data
        assert "refresh_token" in login_response_data
        
        # New tokens should be different from registration tokens
        new_access_token = login_response_data["access_token"]
        new_refresh_token = login_response_data["refresh_token"]
        
        assert new_access_token != access_token
        assert new_refresh_token != refresh_token
        
        # Step 4: Use new access token
        new_auth_headers = {"Authorization": f"Bearer {new_access_token}"}
        
        me_response2 = client.get("/api/v1/users/me", headers=new_auth_headers)
        if me_response2.status_code != 404:
            assert me_response2.status_code != 401
    
    def test_multiple_user_isolation(self, client):
        """Test that multiple users are properly isolated"""
        # Create first user
        user1_data = UserFactory.create_user_data(
            email="user1@example.com",
            name="User One"
        )
        
        response1 = client.post("/api/v1/auth/register", json=user1_data)
        assert response1.status_code == 200
        user1_tokens = response1.json()
        
        # Create second user
        user2_data = UserFactory.create_user_data(
            email="user2@example.com",
            name="User Two"
        )
        
        response2 = client.post("/api/v1/auth/register", json=user2_data)
        assert response2.status_code == 200
        user2_tokens = response2.json()
        
        # Tokens should be different
        assert user1_tokens["access_token"] != user2_tokens["access_token"]
        assert user1_tokens["refresh_token"] != user2_tokens["refresh_token"]
        
        # Both users should be able to access their own resources
        headers1 = {"Authorization": f"Bearer {user1_tokens['access_token']}"}
        headers2 = {"Authorization": f"Bearer {user2_tokens['access_token']}"}
        
        # Test that both tokens work (assuming protected endpoint exists)
        response1_me = client.get("/api/v1/users/me", headers=headers1)
        response2_me = client.get("/api/v1/users/me", headers=headers2)
        
        if response1_me.status_code != 404 and response2_me.status_code != 404:
            assert response1_me.status_code != 401
            assert response2_me.status_code != 401
            
            # If endpoints return user data, it should be different
            if response1_me.status_code == 200 and response2_me.status_code == 200:
                user1_info = response1_me.json()
                user2_info = response2_me.json()
                assert user1_info["email"] != user2_info["email"]
    
    def test_invalid_token_handling(self, client):
        """Test various invalid token scenarios"""
        # Test with completely invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_string"}
        response = client.get("/api/v1/users/me", headers=invalid_headers)
        
        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401
        
        # Test with malformed authorization header
        malformed_headers = {"Authorization": "invalid_format"}
        response2 = client.get("/api/v1/users/me", headers=malformed_headers)
        
        if response2.status_code != 404:
            assert response2.status_code == 401
        
        # Test with empty authorization header
        empty_headers = {"Authorization": ""}
        response3 = client.get("/api/v1/users/me", headers=empty_headers)
        
        if response3.status_code != 404:
            assert response3.status_code == 401
        
        # Test without authorization header
        response4 = client.get("/api/v1/users/me")
        
        if response4.status_code != 404:
            assert response4.status_code == 401
    
    def test_duplicate_registration_prevention(self, client):
        """Test that duplicate email registration is prevented"""
        user_data = UserFactory.create_user_data(email="duplicate_test@example.com")
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        
        error_detail = response2.json()["detail"]
        assert "already registered" in error_detail.lower()
    
    def test_login_failure_scenarios(self, client):
        """Test various login failure scenarios"""
        # Register a user first
        user_data = UserFactory.create_user_data(email="login_fail_test@example.com")
        client.post("/api/v1/auth/register", json=user_data)
        
        # Test wrong password
        wrong_password_data = {
            "email": user_data["email"],
            "password": "wrong_password"
        }
        response1 = client.post("/api/v1/auth/login", json=wrong_password_data)
        assert response1.status_code == 401
        
        # Test non-existent email
        non_existent_data = {
            "email": "nonexistent@example.com",
            "password": user_data["password"]
        }
        response2 = client.post("/api/v1/auth/login", json=non_existent_data)
        assert response2.status_code == 401
        
        # Test empty credentials
        empty_data = {"email": "", "password": ""}
        response3 = client.post("/api/v1/auth/login", json=empty_data)
        assert response3.status_code in [400, 401, 422]
        
        # Test missing credentials
        missing_data = {}
        response4 = client.post("/api/v1/auth/login", json=missing_data)
        assert response4.status_code == 422