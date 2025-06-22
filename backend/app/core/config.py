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
        """Get environment-specific database path"""
        # Check if DB_PATH is explicitly set
        if os.getenv("DB_PATH"):
            return os.getenv("DB_PATH")
        
        # Debug: Log all environment variables for diagnosis
        railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME")
        regular_env = os.getenv("ENVIRONMENT")
        print(f"🐛 DEBUG - RAILWAY_ENVIRONMENT_NAME: '{railway_env}'")
        print(f"🐛 DEBUG - ENVIRONMENT: '{regular_env}'")
        print(f"🐛 DEBUG - Final ENVIRONMENT: '{self.ENVIRONMENT}'")
        
        # Use environment-specific database files
        env_lower = self.ENVIRONMENT.lower()
        
        # Handle Railway's specific environment names
        if "production" in env_lower or env_lower == "prod":
            db_name = "production_food_app.db"
        elif "preview" in env_lower or "staging" in env_lower:
            db_name = "preview_food_app.db"
        elif "test" in env_lower:
            db_name = "test_food_app.db"
        else:
            # Fallback: use environment name as prefix
            db_name = f"{env_lower}_food_app.db"
        
        print(f"🐛 DEBUG - Database file: '{db_name}'")
        return db_name
    
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
