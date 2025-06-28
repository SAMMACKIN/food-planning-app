"""
Main FastAPI application instance and configuration
"""
import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import init_database, populate_sample_data, ensure_separate_databases, verify_database_schema


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Food Planning App API...")
    ensure_separate_databases()
    init_database()
    populate_sample_data()
    
    # Final verification
    if not verify_database_schema():
        logger.error("❌ Database schema verification failed during startup")
        raise RuntimeError("Database not properly configured")
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Food Planning App API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="AI-powered meal planning and family nutrition management",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Import and include routers with error handling
    try:
        from .api import auth, family, pantry, recommendations, meal_plans, recipes, admin
        
        app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
        app.include_router(family.router, prefix="/api/v1", tags=["family"])
        app.include_router(pantry.router, prefix="/api/v1", tags=["pantry"])
        app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
        app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
        app.include_router(meal_plans.router, prefix="/api/v1", tags=["meal-plans"])
        app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
        
        logger.info("✅ All routers imported and registered successfully")
        logger.info(f"📝 Recipes router registered at: /api/v1/recipes")
        
    except Exception as e:
        logger.error(f"❌ Error importing/registering routers: {e}")
        raise
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "deployment_info": settings.deployment_info,
            "version": settings.VERSION
        }
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": settings.APP_NAME}
    
    @app.get("/api/v1/debug/app-version")
    async def debug_app_version():
        """Debug endpoint to confirm which app is running"""
        return {
            "app": "modular_app (app.main:app)",
            "has_recipes_endpoint": True,
            "recipes_router_included": True,
            "available_routes": [route.path for route in app.routes if hasattr(route, 'path')],
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    return app


# Create the app instance
app = create_app()