"""
Application configuration management
"""
import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings"""
    
    # Database
    DB_PATH: str = os.getenv("DB_PATH", "simple_food_app.db")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "fallback-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Local development
        "https://food-planning-app.vercel.app",  # Production frontend
        "https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app",  # Preview frontend
    ]
    
    # Claude AI
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # App info
    APP_NAME: str = "Food Planning App API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
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
