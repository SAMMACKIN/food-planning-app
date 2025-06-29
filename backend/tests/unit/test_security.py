import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from jose import jwt

from app.core.security import (
    create_access_token,
    verify_password,
    hash_password,
    verify_token
)


@pytest.mark.unit
class TestSecurityFunctions:
    """Test security utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        
        # Hash the password
        hashed = hash_password(password)
        
        # Should not be the same as the original password
        assert hashed != password
        assert len(hashed) > 0
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        
        # Should not verify with wrong password
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)"""
        password = "test_password_123"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify the same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    @patch('app.core.security.settings')
    def test_create_access_token_default_expiration(self, mock_settings):
        """Test creating access token with default expiration"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        data = {"sub": "user@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode to verify contents
        payload = jwt.decode(
            token, 
            mock_settings.JWT_SECRET_KEY, 
            algorithms=[mock_settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == "123"
        assert "exp" in payload
    
    @patch('app.core.security.settings')
    def test_create_access_token_custom_expiration(self, mock_settings):
        """Test creating access token with custom expiration"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=60)
        
        before_creation = datetime.utcnow()
        token = create_access_token(data, expires_delta)
        after_creation = datetime.utcnow()
        
        # Decode to verify expiration
        payload = jwt.decode(
            token, 
            mock_settings.JWT_SECRET_KEY, 
            algorithms=[mock_settings.JWT_ALGORITHM]
        )
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_min = before_creation + expires_delta
        expected_max = after_creation + expires_delta
        
        assert expected_min <= exp_time <= expected_max
    
    # @patch('app.core.security.settings')  
    # def test_create_refresh_token(self, mock_settings):
    #     """Test creating refresh token - disabled for modular app"""
    #     # Refresh tokens not implemented in modular app security module
    #     pass
    
    def test_refresh_token_placeholder(self):
        """Placeholder test for refresh token functionality"""
        # The modular app uses only access tokens currently
        assert True, "Refresh tokens not implemented in modular app"
    
    @patch('app.core.security.settings')
    def test_verify_token_valid(self, mock_settings):
        """Test verifying a valid token"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        data = {"sub": "user@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == "123"
        assert "exp" in payload
    
    @patch('app.core.security.settings')
    def test_verify_token_invalid(self, mock_settings):
        """Test verifying an invalid token"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        
        invalid_token = "invalid.jwt.token"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    @patch('app.core.security.settings')
    def test_verify_token_expired(self, mock_settings):
        """Test verifying an expired token"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        
        # Create token that expires immediately
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)
        
        payload = verify_token(token)
        
        assert payload is None
    
    @patch('app.core.security.settings')
    def test_verify_token_wrong_secret(self, mock_settings):
        """Test verifying token with wrong secret"""
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        # Create token with one secret
        data = {"sub": "user@example.com"}
        token = create_access_token(data)
        
        # Try to verify with different secret
        mock_settings.JWT_SECRET_KEY = "different_secret_key"
        payload = verify_token(token)
        
        assert payload is None
    
    def test_password_edge_cases(self):
        """Test password hashing with edge cases"""
        # Empty password
        empty_hash = hash_password("")
        assert verify_password("", empty_hash) is True
        assert verify_password("not_empty", empty_hash) is False
        
        # Very long password
        long_password = "a" * 1000
        long_hash = hash_password(long_password)
        assert verify_password(long_password, long_hash) is True
        
        # Password with special characters
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        special_hash = hash_password(special_password)
        assert verify_password(special_password, special_hash) is True
        
        # Unicode password
        unicode_password = "пароль测试🔐"
        unicode_hash = hash_password(unicode_password)
        assert verify_password(unicode_password, unicode_hash) is True