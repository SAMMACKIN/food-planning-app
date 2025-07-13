"""
Main FastAPI application instance and configuration
"""
import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database_service import init_db, db_service


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Food Planning App API (PostgreSQL ready) - Preview deployment with AI, ingredients v2, and recipe ratings...")
    logger.info(f"Database URL: {get_settings().DATABASE_URL}")
    init_db()
    logger.info("✅ Database initialization complete")
    
    # Ensure RecipeV2 table exists with correct schema
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
        from ensure_recipes_v2 import ensure_recipes_v2_table
        ensure_recipes_v2_table()
    except Exception as e:
        logger.warning(f"⚠️ RecipeV2 table check failed: {e}")
    
    # Ensure recipe_ratings table exists
    try:
        from ensure_recipe_ratings_table import ensure_recipe_ratings_table
        ensure_recipe_ratings_table()
    except Exception as e:
        logger.warning(f"⚠️ Recipe ratings table check failed: {e}")
    
    # Run database migrations
    try:
        from .migrations.add_dietary_restrictions import add_dietary_restrictions_column
        add_dietary_restrictions_column()
    except Exception as e:
        logger.warning(f"⚠️ Database migration failed: {e}")
    
    # Add expanded ingredients list
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
        from add_expanded_ingredients import add_expanded_ingredients
        add_expanded_ingredients()
    except Exception as e:
        logger.warning(f"⚠️ Expanded ingredients migration failed: {e}")
    
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
    
    # Import and include routers with detailed error handling
    router_status = {}
    
    try:
        # Import each router individually to catch specific import errors
        try:
            from .api import auth
            app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
            router_status["auth"] = "✅ Success"
        except Exception as e:
            router_status["auth"] = f"❌ Failed: {e}"
            logger.error(f"❌ Auth router error: {e}")
        
        try:
            from .api import family
            app.include_router(family.router, prefix="/api/v1", tags=["family"])
            router_status["family"] = "✅ Success"
        except Exception as e:
            router_status["family"] = f"❌ Failed: {e}"
            logger.error(f"❌ Family router error: {e}")
        
        try:
            from .api import pantry
            app.include_router(pantry.router, prefix="/api/v1", tags=["pantry"])
            router_status["pantry"] = "✅ Success"
        except Exception as e:
            router_status["pantry"] = f"❌ Failed: {e}"
            logger.error(f"❌ Pantry router error: {e}")
        
        try:
            from .api import ingredients
            app.include_router(ingredients.router, prefix="/api/v1", tags=["ingredients"])
            router_status["ingredients"] = "✅ Success"
        except Exception as e:
            router_status["ingredients"] = f"❌ Failed: {e}"
            logger.error(f"❌ Ingredients router error: {e}")
        
        try:
            from .api import recommendations
            app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
            router_status["recommendations"] = "✅ Success"
        except Exception as e:
            router_status["recommendations"] = f"❌ Failed: {e}"
            logger.error(f"❌ Recommendations router error: {e}")
        
        try:
            from .api import recipes
            app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
            router_status["recipes"] = "✅ Success"
            logger.info(f"📝 Recipes router registered at: /api/v1/recipes")
        except Exception as e:
            router_status["recipes"] = f"❌ Failed: {e}"
            logger.error(f"❌ Recipes router error: {e}")
        
# Removed recipes_optimized - using single simple recipes implementation
        
        try:
            from .api import meal_plans
            app.include_router(meal_plans.router, prefix="/api/v1", tags=["meal-plans"])
            router_status["meal_plans"] = "✅ Success"
        except Exception as e:
            router_status["meal_plans"] = f"❌ Failed: {e}"
            logger.error(f"❌ Meal plans router error: {e}")
        
        try:
            from .api import admin
            app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
            router_status["admin"] = "✅ Success"
        except Exception as e:
            router_status["admin"] = f"❌ Failed: {e}"
            logger.error(f"❌ Admin router error: {e}")
        
        # Migration endpoints for database schema updates
        try:
            from .api import migrate
            app.include_router(migrate.router, prefix="/api/v1/migrate", tags=["migration"])
            router_status["migrate"] = "✅ Success"
        except Exception as e:
            router_status["migrate"] = f"❌ Failed: {e}"
            logger.error(f"❌ Migration router error: {e}")
        
        logger.info(f"🔧 Router registration status: {router_status}")
        
    except Exception as e:
        logger.error(f"❌ Critical error in router setup: {e}")
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
    
    @app.get("/debug/routes")
    async def debug_routes():
        """Debug endpoint to show all registered routes"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                route_info = {
                    "path": route.path,
                    "methods": getattr(route, 'methods', None),
                    "name": getattr(route, 'name', None)
                }
                routes.append(route_info)
        
        return {
            "app": "modular_app (app.main:app)",
            "total_routes": len(routes),
            "routes": routes,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    return app


# Create the app instance
app = create_app()