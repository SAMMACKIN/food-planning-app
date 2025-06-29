#!/usr/bin/env python3
"""
Simple test runner for testing framework components without full app initialization
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Test security functions
def test_security_functions():
    """Test security functions directly"""
    from app.core.security import get_password_hash, verify_password, create_access_token, verify_token
    from datetime import timedelta
    
    print("Testing password hashing...")
    password = "test_password_123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    print("✓ Password hashing works")
    
    print("Testing JWT tokens...")
    # Mock settings for token testing
    import app.core.security
    
    # Create a test token
    data = {"sub": "test@example.com", "user_id": "123"}
    token = create_access_token(data, timedelta(minutes=5))
    assert token is not None
    assert len(token) > 0
    print("✓ Token creation works")
    
    # Verify the token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["user_id"] == "123"
    print("✓ Token verification works")
    
    print("All security tests passed!")

def test_config():
    """Test configuration"""
    from app.core.config import Settings
    
    print("Testing configuration...")
    settings = Settings()
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_EXPIRATION_HOURS == 24
    assert settings.APP_NAME == "Food Planning App API"
    print("✓ Configuration works")

if __name__ == "__main__":
    print("Running basic component tests...")
    test_config()
    test_security_functions()
    print("All tests passed!")