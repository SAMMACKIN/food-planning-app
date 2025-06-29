"""
Application configuration management
"""
import os
import logging
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger for configuration
logger = logging.getLogger(__name__)


class Settings:
    """Application settings"""
    
    def __init__(self):
        """Initialize and validate settings"""
        # Database - Environment-specific database paths
        self.ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT_NAME", os.getenv("ENVIRONMENT", "development"))
        
        # Security
        self.JWT_SECRET: str = os.getenv("JWT_SECRET")
        self.JWT_ALGORITHM: str = "HS256"
        self.JWT_EXPIRATION_HOURS: int = 24
        
        # Validate critical security settings
        if not self.JWT_SECRET:
            # Allow fallback in test environments only
            if os.getenv("TESTING") == "true" or os.getenv("CI") == "true":
                self.JWT_SECRET = "test-jwt-secret-for-testing-environments-only"
                logger.warning("Using fallback JWT_SECRET for test/CI environment")
            else:
                raise ValueError(
                    "JWT_SECRET environment variable is required for security. "
                    "Set JWT_SECRET=your-secure-secret-key in your environment."
                )
    
    @property
    def DB_PATH(self) -> str:
        """Get environment-specific database path for modular app"""
        # Check if DB_PATH is explicitly set
        if os.getenv("DB_PATH"):
            return os.getenv("DB_PATH")
        
        # Use consistent database path logic across environments
        env_lower = self.ENVIRONMENT.lower()
        
        # Check Railway environment variables for deployment detection
        railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').lower()
        is_railway = bool(railway_domain or os.getenv('RAILWAY_PROJECT_ID'))
        
        if is_railway:
            # Use domain-based detection for Railway environments
            if 'preview' in railway_domain or 'preview' in env_lower:
                return '/app/data/preview_food_app.db'
            elif 'production' in railway_domain or env_lower == 'production':
                return '/app/data/production_food_app.db'
            else:
                # Fallback: assume production for Railway
                return '/app/data/production_food_app.db'
        else:
            # Local development
            return 'development_food_app.db'
    
        # CORS
        self.CORS_ORIGINS: list = [
            "http://localhost:3000",  # Local development
            "https://food-planning-app.vercel.app",  # Production frontend
            "https://food-planning-app-preview.vercel.app",  # New preview frontend
            "https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app",  # Old preview frontend (legacy)
        ]
        
        # Claude AI
        self.ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        
        # App info
        self.APP_NAME: str = "Food Planning App API"
        self.VERSION: str = "1.0.0"
        
        # Deployment info
        self.RAILWAY_DEPLOYMENT_ID: Optional[str] = os.getenv("RAILWAY_DEPLOYMENT_ID")
        self.RAILWAY_DEPLOYMENT_DOMAIN: Optional[str] = os.getenv("RAILWAY_DEPLOYMENT_DOMAIN")
    
    @property
    def deployment_info(self) -> dict:
        """Get deployment information"""
        return {
            "deployment_id": self.RAILWAY_DEPLOYMENT_ID,
            "domain": self.RAILWAY_DEPLOYMENT_DOMAIN,
            "environment": self.ENVIRONMENT
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Legacy compatibility - maintain existing imports
# Note: These are loaded lazily when first accessed
try:
    _settings = get_settings()
    JWT_SECRET = _settings.JWT_SECRET
    JWT_ALGORITHM = _settings.JWT_ALGORITHM
except Exception:
    # Fallback for import-time issues
    JWT_SECRET = None
    JWT_ALGORITHM = "HS256"
