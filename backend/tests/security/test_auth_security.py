"""
Security tests for authentication system
"""
import os
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

# Import from simple_app since we're testing the monolith
import simple_app


class TestPasswordSecurity:
    """Test password hashing security improvements"""
    
    def test_password_hashing_bcrypt(self):
        """Test that passwords are hashed using bcrypt"""
        password = "test_password_123"
        hashed = simple_app.hash_password(password)
        
        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$"), "Password should be hashed with bcrypt"
        assert len(hashed) >= 60, "Bcrypt hash should be at least 60 characters"
        assert hashed != password, "Password should not be stored in plain text"
    
    def test_password_verification_bcrypt(self):
        """Test that password verification works with bcrypt"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        
        hashed = simple_app.hash_password(password)
        
        # Correct password should verify
        assert simple_app.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert simple_app.verify_password(wrong_password, hashed) is False
    
    def test_password_hash_unique(self):
        """Test that identical passwords produce different hashes (salt)"""
        password = "same_password"
        hash1 = simple_app.hash_password(password)
        hash2 = simple_app.hash_password(password)
        
        # Same password should produce different hashes due to salt
        assert hash1 != hash2, "Bcrypt should use salt to produce unique hashes"


class TestJWTSecurity:
    """Test JWT token security improvements"""
    
    def test_jwt_secret_from_environment(self):
        """Test that JWT secret is loaded from environment"""
        # Test that JWT_SECRET is not the hardcoded 'secret'
        assert simple_app.JWT_SECRET != 'secret', "JWT secret should not be hardcoded 'secret'"
        assert len(simple_app.JWT_SECRET) >= 32, "JWT secret should be at least 32 characters"
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-for-testing-12345'})
    def test_jwt_uses_environment_secret(self):
        """Test that JWT creation uses environment variable"""
        # Reload the module to pick up the environment variable
        import importlib
        importlib.reload(simple_app)
        
        user_id = "test_user_123"
        token = simple_app.create_token(user_id)
        
        # Verify token was created with environment secret
        payload = jwt.decode(token, 'test-secret-for-testing-12345', algorithms=['HS256'])
        assert payload['sub'] == user_id
    
    def test_token_expiration(self):
        """Test that tokens have proper expiration"""
        user_id = "test_user_123"
        token = simple_app.create_token(user_id)
        
        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Should have expiration time
        assert 'exp' in payload, "Token should have expiration time"
        assert 'iat' in payload, "Token should have issued at time"
        
        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(payload['exp'])
        assert exp_time > datetime.utcnow(), "Token should expire in the future"
    
    def test_token_verification_invalid_secret(self):
        """Test that tokens can't be verified with wrong secret"""
        user_id = "test_user_123"
        token = simple_app.create_token(user_id)
        
        # Try to verify with wrong secret - should fail
        with patch.object(simple_app, 'JWT_SECRET', 'wrong-secret'):
            result = simple_app.verify_token(token)
            assert result is None, "Token should not verify with wrong secret"
    
    def test_expired_token_handling(self):
        """Test that expired tokens are properly rejected"""
        user_id = "test_user_123"
        
        # Create token that's already expired
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, simple_app.JWT_SECRET, algorithm=simple_app.JWT_ALGORITHM)
        
        # Should return None for expired token
        result = simple_app.verify_token(expired_token)
        assert result is None, "Expired token should be rejected"


class TestCORSSecurity:
    """Test CORS security improvements"""
    
    def test_cors_restricted_origins(self):
        """Test that CORS origins are restricted to specific domains"""
        # Should not contain wildcard patterns
        assert not any('*' in origin for origin in simple_app.ALLOWED_ORIGINS), \
            "CORS should not contain wildcard origins"
        
        # Should contain expected domains
        expected_domains = [
            "http://localhost:3000",
            "https://food-planning-app.vercel.app"
        ]
        
        for domain in expected_domains:
            assert domain in simple_app.ALLOWED_ORIGINS, f"Missing expected CORS origin: {domain}"
    
    def test_cors_environment_variable_support(self):
        """Test that additional CORS origins can be added via environment"""
        with patch.dict(os.environ, {'ADDITIONAL_CORS_ORIGINS': 'https://test1.com,https://test2.com'}):
            # Reload CORS configuration
            import importlib
            importlib.reload(simple_app)
            
            assert 'https://test1.com' in simple_app.ALLOWED_ORIGINS
            assert 'https://test2.com' in simple_app.ALLOWED_ORIGINS


class TestGeneralSecurity:
    """Test general security improvements"""
    
    def test_no_hardcoded_secrets(self):
        """Test that no hardcoded secrets remain in the code"""
        # Read the source file to check for hardcoded secrets
        with open('simple_app.py', 'r') as f:
            content = f.read()
        
        # Should not contain the old hardcoded 'secret'
        assert "jwt.encode(payload, 'secret'" not in content, \
            "Source should not contain hardcoded JWT secret"
        
        # Should not contain SHA256 password hashing
        assert "hashlib.sha256(password" not in content, \
            "Source should not use SHA256 for password hashing"
    
    def test_secure_defaults(self):
        """Test that secure defaults are in place"""
        # JWT algorithm should be secure
        assert simple_app.JWT_ALGORITHM == 'HS256', "Should use HS256 algorithm"
        
        # Password context should use bcrypt
        assert 'bcrypt' in simple_app.pwd_context.schemes(), "Should use bcrypt for passwords"
    
    def test_security_logging(self):
        """Test that security events are logged"""
        # This would be expanded to test actual security logging
        # For now, just verify that logging is configured
        assert hasattr(simple_app, 'logger'), "Should have logger configured"