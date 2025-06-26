"""
Main FastAPI application instance and configuration
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import init_database, populate_sample_data, ensure_separate_databases, verify_database_schema, repair_database_schema


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
    
    # Final verification with automatic repair
    if not verify_database_schema():
        logger.warning("⚠️ Database schema verification failed during startup, attempting repair...")
        if repair_database_schema():
            logger.info("✅ Schema repair successful, re-verifying...")
            if verify_database_schema():
                logger.info("✅ Database schema verification passed after repair")
            else:
                logger.error("❌ Database schema verification still failing after repair")
                raise RuntimeError("Database schema verification failed even after repair")
        else:
            logger.error("❌ Database schema repair failed during startup")
            raise RuntimeError("Database schema repair failed")
    
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
    
    # Import and include routers
    from .api import auth, family, pantry, recommendations, meal_plans, recipes, admin
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(family.router, prefix="/api/v1", tags=["family"])
    app.include_router(pantry.router, prefix="/api/v1", tags=["pantry"])
    app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
    app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
    app.include_router(meal_plans.router, prefix="/api/v1", tags=["meal-plans"])
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    
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
    
    return app


# Create the app instance
app = create_app()