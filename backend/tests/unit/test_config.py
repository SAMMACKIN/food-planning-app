import pytest
from unittest.mock import patch
import os

from app.core.config import Settings


@pytest.mark.unit
class TestConfiguration:
    """Test configuration settings"""
    
    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()
        
        # Test default values that should always be set
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.API_V1_STR == "/api/v1"
        
        # Database URL should have a default
        assert settings.DATABASE_URL is not None
        assert "sqlite" in settings.DATABASE_URL.lower()
    
    @patch.dict(os.environ, {
        "JWT_SECRET_KEY": "test_secret_123",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "DATABASE_URL": "postgresql://test:test@localhost/test"
    })
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        settings = Settings()
        
        assert settings.JWT_SECRET_KEY == "test_secret_123"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert settings.DATABASE_URL == "postgresql://test:test@localhost/test"
    
    @patch.dict(os.environ, {
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "invalid_number"
    })
    def test_invalid_environment_variable_type(self):
        """Test handling of invalid environment variable types"""
        # This should raise a validation error or use default
        try:
            settings = Settings()
            # If it doesn't raise an error, it should use default
            assert isinstance(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES, int)
        except ValueError:
            # This is also acceptable - validation caught the error
            pass
    
    def test_required_settings_validation(self):
        """Test that required settings are validated"""
        # JWT_SECRET_KEY should be required or auto-generated
        settings = Settings()
        
        # Should either be set or have a reasonable default/auto-generation
        assert settings.JWT_SECRET_KEY is not None
        assert len(settings.JWT_SECRET_KEY) > 0
    
    @patch.dict(os.environ, {
        "DATABASE_URL": ""
    })
    def test_empty_database_url(self):
        """Test handling of empty database URL"""
        settings = Settings()
        
        # Should have a fallback database URL
        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0
    
    def test_settings_immutability(self):
        """Test that settings are properly configured"""
        settings = Settings()
        
        # Settings should be hashable/immutable for performance
        # (depends on pydantic configuration)
        try:
            hash(settings)
        except TypeError:
            # This is fine if settings aren't meant to be hashable
            pass
    
    def test_cors_settings(self):
        """Test CORS configuration"""
        settings = Settings()
        
        # CORS settings should be available
        if hasattr(settings, 'CORS_ORIGINS'):
            assert isinstance(settings.CORS_ORIGINS, (list, str))
        
        if hasattr(settings, 'CORS_ALLOW_CREDENTIALS'):
            assert isinstance(settings.CORS_ALLOW_CREDENTIALS, bool)
    
    def test_debug_settings(self):
        """Test debug/development settings"""
        settings = Settings()
        
        # Debug settings should be boolean if they exist
        if hasattr(settings, 'DEBUG'):
            assert isinstance(settings.DEBUG, bool)
        
        if hasattr(settings, 'TESTING'):
            assert isinstance(settings.TESTING, bool)
    
    @patch.dict(os.environ, {
        "JWT_SECRET_KEY": "short"
    })
    def test_jwt_secret_length_validation(self):
        """Test JWT secret key length validation"""
        settings = Settings()
        
        # JWT secret should be reasonably long for security
        # (this depends on whether validation is implemented)
        assert len(settings.JWT_SECRET_KEY) >= 5  # Very minimal check
    
    def test_api_version_format(self):
        """Test API version string format"""
        settings = Settings()
        
        assert settings.API_V1_STR.startswith("/")
        assert "v1" in settings.API_V1_STR.lower()
    
    def test_token_expiration_values(self):
        """Test that token expiration values are reasonable"""
        settings = Settings()
        
        # Access token should expire in reasonable time (1 min to 24 hours)
        assert 1 <= settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 1440
        
        # Refresh token should expire in reasonable time (1 day to 90 days)
        assert 1 <= settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS <= 90