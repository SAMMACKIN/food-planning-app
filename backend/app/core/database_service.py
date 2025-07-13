"""
Unified database service layer supporting both SQLite and PostgreSQL
"""
import logging
import os
from contextlib import contextmanager
from typing import Optional, Any, Dict, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from ..db.database import Base, get_db  # SQLAlchemy setup
from .. import models  # Import all models so Base.metadata knows about them

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service using SQLAlchemy (supports SQLite and PostgreSQL)"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize SQLAlchemy engine
        connect_args = {}
        engine_kwargs = {
            "echo": False  # Set to True for SQL logging
        }
        
        if self.settings.DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        else:
            engine_kwargs.update({
                "pool_pre_ping": True,
                "pool_recycle": 300
            })
        
        self.engine = create_engine(
            self.settings.DATABASE_URL,
            connect_args=connect_args,
            **engine_kwargs
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"📊 Database service initialized: {self.settings.DATABASE_URL}")
    
    @contextmanager
    def get_session(self):
        """Get database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ Database tables created")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database service instance
db_service = DatabaseService()


@contextmanager
def get_db_session():
    """Global function to get database session"""
    with db_service.get_session() as session:
        yield session


def init_db():
    """Initialize database tables"""
    db_service.create_tables()
    
    # Create admin user if it doesn't exist
    from .auth_service import AuthService
    admin_user = AuthService.get_user_by_email("admin")
    if not admin_user:
        logger.info("🔑 Creating admin user...")
        admin_user = AuthService.create_user(
            email="admin",
            name="Admin User",
            password="admin123",
            is_admin=True
        )
        if admin_user:
            logger.info("✅ Admin user created successfully")
        else:
            logger.error("❌ Failed to create admin user")
    else:
        logger.info("✅ Admin user already exists")
    
    # Seed default data
    _seed_default_data()


def _seed_default_data():
    """Seed database with default ingredients and categories"""
    try:
        with get_db_session() as session:
            from ..models.ingredient import IngredientCategory, Ingredient
            from ..data.ingredients_data import INGREDIENT_CATEGORIES, INGREDIENTS_DATA
            
            # Check if categories already exist
            existing_categories = session.query(IngredientCategory).count()
            if existing_categories > 0:
                logger.info("✅ Default ingredients already seeded")
                return
            
            logger.info("🌱 Seeding default ingredient categories and ingredients...")
            
            # Create categories using centralized data
            category_objects = {}
            for cat_name in INGREDIENT_CATEGORIES:
                category = IngredientCategory(name=cat_name)
                session.add(category)
                session.flush()  # Get the ID
                category_objects[cat_name] = category
            
            # Create ingredients using centralized data
            for name, category_name, unit, nutrition in INGREDIENTS_DATA:
                ingredient = Ingredient(
                    name=name,
                    category_id=category_objects[category_name].id,
                    unit=unit,
                    nutritional_info=nutrition,
                    allergens=[]
                )
                session.add(ingredient)
            
            logger.info(f"✅ Seeded {len(INGREDIENT_CATEGORIES)} categories and {len(INGREDIENTS_DATA)} ingredients")
            
    except Exception as e:
        logger.error(f"❌ Error seeding default data: {e}")


def test_db_connection() -> bool:
    """Test database connection"""
    return db_service.test_connection()