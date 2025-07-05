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
# Removed SQLite imports - now PostgreSQL only
from ..db.database import Base, get_db  # SQLAlchemy setup
from .. import models  # Import all models so Base.metadata knows about them

logger = logging.getLogger(__name__)


class DatabaseService:
    """PostgreSQL database service using SQLAlchemy"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize SQLAlchemy engine for PostgreSQL
        self.engine = create_engine(
            self.settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Set to True for SQL logging
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"🐘 Database service initialized with PostgreSQL: {self.settings.DATABASE_URL}")
    
    @contextmanager
    def get_session(self):
        """Get PostgreSQL database session"""
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
        """Create PostgreSQL database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ PostgreSQL tables created")
    
    def test_connection(self) -> bool:
        """Test PostgreSQL database connection"""
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
            
            # Check if categories already exist
            existing_categories = session.query(IngredientCategory).count()
            if existing_categories > 0:
                logger.info("✅ Default ingredients already seeded")
                return
            
            logger.info("🌱 Seeding default ingredient categories and ingredients...")
            
            # Create categories
            categories = [
                "Proteins", "Vegetables", "Fruits", "Grains", "Dairy", 
                "Spices & Herbs", "Oils & Condiments", "Nuts & Seeds", "Beverages"
            ]
            
            category_objects = {}
            for cat_name in categories:
                category = IngredientCategory(name=cat_name)
                session.add(category)
                session.flush()  # Get the ID
                category_objects[cat_name] = category
            
            # Create common ingredients
            ingredients_data = [
                # Proteins
                ("Chicken Breast", "Proteins", "grams", {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6}),
                ("Ground Beef", "Proteins", "grams", {"calories": 250, "protein": 26, "carbs": 0, "fat": 15}),
                ("Salmon", "Proteins", "grams", {"calories": 208, "protein": 20, "carbs": 0, "fat": 12}),
                ("Eggs", "Proteins", "pieces", {"calories": 70, "protein": 6, "carbs": 1, "fat": 5}),
                ("Black Beans", "Proteins", "cups", {"calories": 227, "protein": 15, "carbs": 41, "fat": 1}),
                
                # Vegetables  
                ("Onion", "Vegetables", "pieces", {"calories": 40, "protein": 1, "carbs": 9, "fat": 0}),
                ("Garlic", "Vegetables", "cloves", {"calories": 4, "protein": 0.2, "carbs": 1, "fat": 0}),
                ("Bell Pepper", "Vegetables", "pieces", {"calories": 25, "protein": 1, "carbs": 6, "fat": 0}),
                ("Broccoli", "Vegetables", "cups", {"calories": 25, "protein": 3, "carbs": 5, "fat": 0}),
                ("Spinach", "Vegetables", "cups", {"calories": 7, "protein": 1, "carbs": 1, "fat": 0}),
                ("Carrots", "Vegetables", "pieces", {"calories": 25, "protein": 1, "carbs": 6, "fat": 0}),
                ("Tomatoes", "Vegetables", "pieces", {"calories": 18, "protein": 1, "carbs": 4, "fat": 0}),
                
                # Fruits
                ("Bananas", "Fruits", "pieces", {"calories": 105, "protein": 1, "carbs": 27, "fat": 0}),
                ("Apples", "Fruits", "pieces", {"calories": 95, "protein": 0, "carbs": 25, "fat": 0}),
                ("Lemons", "Fruits", "pieces", {"calories": 15, "protein": 0, "carbs": 5, "fat": 0}),
                
                # Grains
                ("Rice", "Grains", "cups", {"calories": 130, "protein": 3, "carbs": 28, "fat": 0}),
                ("Pasta", "Grains", "cups", {"calories": 220, "protein": 8, "carbs": 44, "fat": 1}),
                ("Bread", "Grains", "slices", {"calories": 80, "protein": 3, "carbs": 15, "fat": 1}),
                ("Oats", "Grains", "cups", {"calories": 150, "protein": 5, "carbs": 27, "fat": 3}),
                
                # Dairy
                ("Milk", "Dairy", "cups", {"calories": 150, "protein": 8, "carbs": 12, "fat": 8}),
                ("Cheese", "Dairy", "grams", {"calories": 113, "protein": 7, "carbs": 1, "fat": 9}),
                ("Yogurt", "Dairy", "cups", {"calories": 150, "protein": 8, "carbs": 17, "fat": 8}),
                ("Butter", "Dairy", "tablespoons", {"calories": 102, "protein": 0, "carbs": 0, "fat": 12}),
                
                # Spices & Herbs
                ("Salt", "Spices & Herbs", "teaspoons", {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}),
                ("Black Pepper", "Spices & Herbs", "teaspoons", {"calories": 6, "protein": 0, "carbs": 1, "fat": 0}),
                ("Basil", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Oregano", "Spices & Herbs", "teaspoons", {"calories": 3, "protein": 0, "carbs": 1, "fat": 0}),
                
                # Oils & Condiments
                ("Olive Oil", "Oils & Condiments", "tablespoons", {"calories": 119, "protein": 0, "carbs": 0, "fat": 14}),
                ("Soy Sauce", "Oils & Condiments", "tablespoons", {"calories": 10, "protein": 2, "carbs": 1, "fat": 0}),
                ("Vinegar", "Oils & Condiments", "tablespoons", {"calories": 3, "protein": 0, "carbs": 0, "fat": 0}),
                
                # Nuts & Seeds
                ("Almonds", "Nuts & Seeds", "grams", {"calories": 579, "protein": 21, "carbs": 22, "fat": 50}),
                ("Walnuts", "Nuts & Seeds", "grams", {"calories": 654, "protein": 15, "carbs": 14, "fat": 65}),
            ]
            
            for name, category_name, unit, nutrition in ingredients_data:
                ingredient = Ingredient(
                    name=name,
                    category_id=category_objects[category_name].id,
                    unit=unit,
                    nutritional_info=nutrition,
                    allergens=[]
                )
                session.add(ingredient)
            
            logger.info(f"✅ Seeded {len(categories)} categories and {len(ingredients_data)} ingredients")
            
    except Exception as e:
        logger.error(f"❌ Error seeding default data: {e}")


def test_db_connection() -> bool:
    """Test database connection"""
    return db_service.test_connection()