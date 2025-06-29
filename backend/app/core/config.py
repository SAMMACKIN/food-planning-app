"""
Application configuration management
"""
import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings"""
    
    # Database - Environment-specific database paths
    ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT_NAME", os.getenv("ENVIRONMENT", "development"))
    
    @property
    def DB_PATH(self) -> str:
        """Get environment-specific database path matching simple_app.py format"""
        # Check if DB_PATH is explicitly set
        if os.getenv("DB_PATH"):
            return os.getenv("DB_PATH")
        
        # Use the SAME database path logic as simple_app.py to eliminate dual DB issue
        env_lower = self.ENVIRONMENT.lower()
        
        # Check Railway environment variables (matching simple_app.py logic)
        railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').lower()
        is_railway = bool(railway_domain or os.getenv('RAILWAY_PROJECT_ID'))
        
        if is_railway:
            # Use domain-based detection (matching simple_app.py)
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
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "fallback-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Local development
        "https://food-planning-app.vercel.app",  # Production frontend
        "https://food-planning-app-preview.vercel.app",  # New preview frontend
        "https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app",  # Old preview frontend (legacy)
    ]
    
    # Claude AI
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # App info
    APP_NAME: str = "Food Planning App API"
    VERSION: str = "1.0.0"
    
    # Deployment info
    RAILWAY_DEPLOYMENT_ID: Optional[str] = os.getenv("RAILWAY_DEPLOYMENT_ID")
    RAILWAY_DEPLOYMENT_DOMAIN: Optional[str] = os.getenv("RAILWAY_DEPLOYMENT_DOMAIN")
    
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
JWT_SECRET = get_settings().JWT_SECRET
JWT_ALGORITHM = get_settings().JWT_ALGORITHM
