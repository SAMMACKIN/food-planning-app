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
            
            # Create common ingredients - expanded list with 140+ ingredients
            ingredients_data = [
                # Proteins
                ("Chicken Breast", "Proteins", "grams", {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6}),
                ("Chicken Thighs", "Proteins", "grams", {"calories": 209, "protein": 26, "carbs": 0, "fat": 11}),
                ("Ground Beef", "Proteins", "grams", {"calories": 250, "protein": 26, "carbs": 0, "fat": 15}),
                ("Ground Turkey", "Proteins", "grams", {"calories": 203, "protein": 27, "carbs": 0, "fat": 9}),
                ("Pork Chops", "Proteins", "grams", {"calories": 231, "protein": 23, "carbs": 0, "fat": 14}),
                ("Salmon", "Proteins", "grams", {"calories": 208, "protein": 20, "carbs": 0, "fat": 12}),
                ("Tuna", "Proteins", "grams", {"calories": 144, "protein": 30, "carbs": 0, "fat": 1}),
                ("Cod", "Proteins", "grams", {"calories": 105, "protein": 23, "carbs": 0, "fat": 1}),
                ("Shrimp", "Proteins", "grams", {"calories": 99, "protein": 18, "carbs": 0, "fat": 1.4}),
                ("Crab", "Proteins", "grams", {"calories": 97, "protein": 19, "carbs": 0, "fat": 1.5}),
                ("Eggs", "Proteins", "pieces", {"calories": 70, "protein": 6, "carbs": 1, "fat": 5}),
                ("Egg Whites", "Proteins", "cups", {"calories": 126, "protein": 26, "carbs": 2, "fat": 0}),
                ("Black Beans", "Proteins", "cups", {"calories": 227, "protein": 15, "carbs": 41, "fat": 1}),
                ("Kidney Beans", "Proteins", "cups", {"calories": 225, "protein": 15, "carbs": 40, "fat": 1}),
                ("Chickpeas", "Proteins", "cups", {"calories": 269, "protein": 15, "carbs": 45, "fat": 4}),
                ("Lentils", "Proteins", "cups", {"calories": 230, "protein": 18, "carbs": 40, "fat": 1}),
                ("Tofu", "Proteins", "grams", {"calories": 76, "protein": 8, "carbs": 2, "fat": 5}),
                ("Tempeh", "Proteins", "grams", {"calories": 193, "protein": 19, "carbs": 9, "fat": 11}),
                ("Greek Yogurt", "Proteins", "cups", {"calories": 100, "protein": 17, "carbs": 6, "fat": 0}),
                ("Cottage Cheese", "Proteins", "cups", {"calories": 163, "protein": 28, "carbs": 6, "fat": 2}),
                ("Protein Powder", "Proteins", "scoops", {"calories": 120, "protein": 25, "carbs": 3, "fat": 1}),
                ("Turkey Breast", "Proteins", "grams", {"calories": 135, "protein": 30, "carbs": 0, "fat": 1}),
                ("Ham", "Proteins", "grams", {"calories": 145, "protein": 21, "carbs": 1, "fat": 6}),
                ("Bacon", "Proteins", "slices", {"calories": 43, "protein": 3, "carbs": 0, "fat": 3}),
                
                # Vegetables  
                ("Onion", "Vegetables", "pieces", {"calories": 40, "protein": 1, "carbs": 9, "fat": 0}),
                ("Red Onion", "Vegetables", "pieces", {"calories": 40, "protein": 1, "carbs": 9, "fat": 0}),
                ("Green Onions", "Vegetables", "cups", {"calories": 32, "protein": 2, "carbs": 7, "fat": 0}),
                ("Garlic", "Vegetables", "cloves", {"calories": 4, "protein": 0.2, "carbs": 1, "fat": 0}),
                ("Ginger", "Vegetables", "tablespoons", {"calories": 4, "protein": 0.1, "carbs": 1, "fat": 0}),
                ("Bell Pepper", "Vegetables", "pieces", {"calories": 25, "protein": 1, "carbs": 6, "fat": 0}),
                ("Red Bell Pepper", "Vegetables", "pieces", {"calories": 30, "protein": 1, "carbs": 7, "fat": 0}),
                ("Jalapeño", "Vegetables", "pieces", {"calories": 4, "protein": 0, "carbs": 1, "fat": 0}),
                ("Broccoli", "Vegetables", "cups", {"calories": 25, "protein": 3, "carbs": 5, "fat": 0}),
                ("Cauliflower", "Vegetables", "cups", {"calories": 25, "protein": 2, "carbs": 5, "fat": 0}),
                ("Brussels Sprouts", "Vegetables", "cups", {"calories": 38, "protein": 3, "carbs": 8, "fat": 0}),
                ("Cabbage", "Vegetables", "cups", {"calories": 22, "protein": 1, "carbs": 5, "fat": 0}),
                ("Spinach", "Vegetables", "cups", {"calories": 7, "protein": 1, "carbs": 1, "fat": 0}),
                ("Kale", "Vegetables", "cups", {"calories": 33, "protein": 2, "carbs": 7, "fat": 0}),
                ("Arugula", "Vegetables", "cups", {"calories": 5, "protein": 1, "carbs": 1, "fat": 0}),
                ("Lettuce", "Vegetables", "cups", {"calories": 5, "protein": 1, "carbs": 1, "fat": 0}),
                ("Carrots", "Vegetables", "pieces", {"calories": 25, "protein": 1, "carbs": 6, "fat": 0}),
                ("Celery", "Vegetables", "cups", {"calories": 16, "protein": 1, "carbs": 3, "fat": 0}),
                ("Cucumber", "Vegetables", "cups", {"calories": 16, "protein": 1, "carbs": 4, "fat": 0}),
                ("Zucchini", "Vegetables", "cups", {"calories": 20, "protein": 1, "carbs": 4, "fat": 0}),
                ("Yellow Squash", "Vegetables", "cups", {"calories": 20, "protein": 1, "carbs": 4, "fat": 0}),
                ("Eggplant", "Vegetables", "cups", {"calories": 20, "protein": 1, "carbs": 5, "fat": 0}),
                ("Tomatoes", "Vegetables", "pieces", {"calories": 18, "protein": 1, "carbs": 4, "fat": 0}),
                ("Cherry Tomatoes", "Vegetables", "cups", {"calories": 27, "protein": 1, "carbs": 6, "fat": 0}),
                ("Mushrooms", "Vegetables", "cups", {"calories": 15, "protein": 2, "carbs": 2, "fat": 0}),
                ("Asparagus", "Vegetables", "cups", {"calories": 27, "protein": 3, "carbs": 5, "fat": 0}),
                ("Green Beans", "Vegetables", "cups", {"calories": 35, "protein": 2, "carbs": 8, "fat": 0}),
                ("Peas", "Vegetables", "cups", {"calories": 134, "protein": 9, "carbs": 25, "fat": 1}),
                ("Corn", "Vegetables", "cups", {"calories": 143, "protein": 5, "carbs": 31, "fat": 2}),
                ("Sweet Potato", "Vegetables", "pieces", {"calories": 112, "protein": 2, "carbs": 26, "fat": 0}),
                ("Regular Potato", "Vegetables", "pieces", {"calories": 161, "protein": 4, "carbs": 37, "fat": 0}),
                ("Beets", "Vegetables", "cups", {"calories": 58, "protein": 2, "carbs": 13, "fat": 0}),
                ("Radishes", "Vegetables", "cups", {"calories": 19, "protein": 1, "carbs": 4, "fat": 0}),
                ("Turnips", "Vegetables", "cups", {"calories": 36, "protein": 1, "carbs": 8, "fat": 0}),
                
                # Fruits
                ("Apples", "Fruits", "pieces", {"calories": 95, "protein": 0, "carbs": 25, "fat": 0}),
                ("Bananas", "Fruits", "pieces", {"calories": 105, "protein": 1, "carbs": 27, "fat": 0}),
                ("Oranges", "Fruits", "pieces", {"calories": 62, "protein": 1, "carbs": 15, "fat": 0}),
                ("Lemons", "Fruits", "pieces", {"calories": 15, "protein": 0, "carbs": 5, "fat": 0}),
                ("Limes", "Fruits", "pieces", {"calories": 20, "protein": 0, "carbs": 7, "fat": 0}),
                ("Grapes", "Fruits", "cups", {"calories": 104, "protein": 1, "carbs": 27, "fat": 0}),
                ("Strawberries", "Fruits", "cups", {"calories": 49, "protein": 1, "carbs": 12, "fat": 0}),
                ("Blueberries", "Fruits", "cups", {"calories": 84, "protein": 1, "carbs": 21, "fat": 0}),
                ("Raspberries", "Fruits", "cups", {"calories": 64, "protein": 1, "carbs": 15, "fat": 1}),
                ("Blackberries", "Fruits", "cups", {"calories": 62, "protein": 2, "carbs": 14, "fat": 1}),
                ("Pineapple", "Fruits", "cups", {"calories": 82, "protein": 1, "carbs": 22, "fat": 0}),
                ("Mango", "Fruits", "cups", {"calories": 107, "protein": 1, "carbs": 28, "fat": 0}),
                ("Peaches", "Fruits", "pieces", {"calories": 59, "protein": 1, "carbs": 14, "fat": 0}),
                ("Pears", "Fruits", "pieces", {"calories": 101, "protein": 1, "carbs": 27, "fat": 0}),
                ("Plums", "Fruits", "pieces", {"calories": 30, "protein": 0, "carbs": 8, "fat": 0}),
                ("Cherries", "Fruits", "cups", {"calories": 97, "protein": 2, "carbs": 25, "fat": 0}),
                ("Watermelon", "Fruits", "cups", {"calories": 46, "protein": 1, "carbs": 12, "fat": 0}),
                ("Cantaloupe", "Fruits", "cups", {"calories": 54, "protein": 1, "carbs": 13, "fat": 0}),
                ("Avocado", "Fruits", "pieces", {"calories": 320, "protein": 4, "carbs": 17, "fat": 29}),
                ("Kiwi", "Fruits", "pieces", {"calories": 42, "protein": 1, "carbs": 10, "fat": 0}),
                
                # Grains
                ("White Rice", "Grains", "cups", {"calories": 130, "protein": 3, "carbs": 28, "fat": 0}),
                ("Brown Rice", "Grains", "cups", {"calories": 112, "protein": 3, "carbs": 23, "fat": 1}),
                ("Wild Rice", "Grains", "cups", {"calories": 166, "protein": 7, "carbs": 35, "fat": 1}),
                ("Quinoa", "Grains", "cups", {"calories": 222, "protein": 8, "carbs": 39, "fat": 4}),
                ("Pasta", "Grains", "cups", {"calories": 220, "protein": 8, "carbs": 44, "fat": 1}),
                ("Whole Wheat Pasta", "Grains", "cups", {"calories": 174, "protein": 7, "carbs": 37, "fat": 1}),
                ("White Bread", "Grains", "slices", {"calories": 80, "protein": 3, "carbs": 15, "fat": 1}),
                ("Whole Wheat Bread", "Grains", "slices", {"calories": 81, "protein": 4, "carbs": 14, "fat": 1}),
                ("Sourdough Bread", "Grains", "slices", {"calories": 93, "protein": 4, "carbs": 18, "fat": 1}),
                ("Bagels", "Grains", "pieces", {"calories": 245, "protein": 10, "carbs": 48, "fat": 2}),
                ("English Muffins", "Grains", "pieces", {"calories": 134, "protein": 4, "carbs": 26, "fat": 1}),
                ("Oats", "Grains", "cups", {"calories": 150, "protein": 5, "carbs": 27, "fat": 3}),
                ("Steel Cut Oats", "Grains", "cups", {"calories": 150, "protein": 5, "carbs": 27, "fat": 3}),
                ("Granola", "Grains", "cups", {"calories": 597, "protein": 18, "carbs": 65, "fat": 29}),
                ("Cereal", "Grains", "cups", {"calories": 110, "protein": 3, "carbs": 22, "fat": 2}),
                ("Crackers", "Grains", "pieces", {"calories": 13, "protein": 0, "carbs": 2, "fat": 1}),
                ("Tortillas", "Grains", "pieces", {"calories": 104, "protein": 3, "carbs": 18, "fat": 2}),
                ("Couscous", "Grains", "cups", {"calories": 176, "protein": 6, "carbs": 36, "fat": 0}),
                ("Barley", "Grains", "cups", {"calories": 193, "protein": 4, "carbs": 44, "fat": 1}),
                
                # Dairy
                ("Whole Milk", "Dairy", "cups", {"calories": 150, "protein": 8, "carbs": 12, "fat": 8}),
                ("2% Milk", "Dairy", "cups", {"calories": 122, "protein": 8, "carbs": 12, "fat": 5}),
                ("Skim Milk", "Dairy", "cups", {"calories": 83, "protein": 8, "carbs": 12, "fat": 0}),
                ("Almond Milk", "Dairy", "cups", {"calories": 39, "protein": 1, "carbs": 4, "fat": 3}),
                ("Soy Milk", "Dairy", "cups", {"calories": 105, "protein": 6, "carbs": 12, "fat": 4}),
                ("Oat Milk", "Dairy", "cups", {"calories": 120, "protein": 3, "carbs": 16, "fat": 5}),
                ("Coconut Milk", "Dairy", "cups", {"calories": 76, "protein": 1, "carbs": 7, "fat": 5}),
                ("Heavy Cream", "Dairy", "tablespoons", {"calories": 51, "protein": 0, "carbs": 0, "fat": 5}),
                ("Sour Cream", "Dairy", "tablespoons", {"calories": 23, "protein": 0, "carbs": 1, "fat": 2}),
                ("Cream Cheese", "Dairy", "tablespoons", {"calories": 51, "protein": 1, "carbs": 1, "fat": 5}),
                ("Cheddar Cheese", "Dairy", "grams", {"calories": 113, "protein": 7, "carbs": 1, "fat": 9}),
                ("Mozzarella Cheese", "Dairy", "grams", {"calories": 85, "protein": 6, "carbs": 1, "fat": 6}),
                ("Parmesan Cheese", "Dairy", "grams", {"calories": 110, "protein": 10, "carbs": 1, "fat": 7}),
                ("Swiss Cheese", "Dairy", "grams", {"calories": 106, "protein": 8, "carbs": 1, "fat": 8}),
                ("Feta Cheese", "Dairy", "grams", {"calories": 75, "protein": 4, "carbs": 1, "fat": 6}),
                ("Regular Yogurt", "Dairy", "cups", {"calories": 150, "protein": 8, "carbs": 17, "fat": 8}),
                ("Greek Yogurt", "Dairy", "cups", {"calories": 100, "protein": 17, "carbs": 6, "fat": 0}),
                ("Cottage Cheese", "Dairy", "cups", {"calories": 163, "protein": 28, "carbs": 6, "fat": 2}),
                ("Ricotta Cheese", "Dairy", "cups", {"calories": 339, "protein": 28, "carbs": 13, "fat": 20}),
                ("Butter", "Dairy", "tablespoons", {"calories": 102, "protein": 0, "carbs": 0, "fat": 12}),
                ("Margarine", "Dairy", "tablespoons", {"calories": 102, "protein": 0, "carbs": 0, "fat": 11}),
                
                # Spices & Herbs
                ("Salt", "Spices & Herbs", "teaspoons", {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}),
                ("Black Pepper", "Spices & Herbs", "teaspoons", {"calories": 6, "protein": 0, "carbs": 1, "fat": 0}),
                ("White Pepper", "Spices & Herbs", "teaspoons", {"calories": 7, "protein": 0, "carbs": 2, "fat": 0}),
                ("Paprika", "Spices & Herbs", "teaspoons", {"calories": 6, "protein": 0, "carbs": 1, "fat": 0}),
                ("Cumin", "Spices & Herbs", "teaspoons", {"calories": 8, "protein": 0, "carbs": 1, "fat": 0}),
                ("Coriander", "Spices & Herbs", "teaspoons", {"calories": 5, "protein": 0, "carbs": 1, "fat": 0}),
                ("Turmeric", "Spices & Herbs", "teaspoons", {"calories": 8, "protein": 0, "carbs": 1, "fat": 0}),
                ("Cinnamon", "Spices & Herbs", "teaspoons", {"calories": 6, "protein": 0, "carbs": 2, "fat": 0}),
                ("Nutmeg", "Spices & Herbs", "teaspoons", {"calories": 12, "protein": 0, "carbs": 1, "fat": 1}),
                ("Cloves", "Spices & Herbs", "teaspoons", {"calories": 7, "protein": 0, "carbs": 1, "fat": 0}),
                ("Allspice", "Spices & Herbs", "teaspoons", {"calories": 5, "protein": 0, "carbs": 1, "fat": 0}),
                ("Bay Leaves", "Spices & Herbs", "pieces", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Basil", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Oregano", "Spices & Herbs", "teaspoons", {"calories": 3, "protein": 0, "carbs": 1, "fat": 0}),
                ("Thyme", "Spices & Herbs", "teaspoons", {"calories": 3, "protein": 0, "carbs": 1, "fat": 0}),
                ("Rosemary", "Spices & Herbs", "teaspoons", {"calories": 4, "protein": 0, "carbs": 1, "fat": 0}),
                ("Sage", "Spices & Herbs", "teaspoons", {"calories": 2, "protein": 0, "carbs": 0, "fat": 0}),
                ("Parsley", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Cilantro", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Dill", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Chives", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Mint", "Spices & Herbs", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Garlic Powder", "Spices & Herbs", "teaspoons", {"calories": 10, "protein": 1, "carbs": 2, "fat": 0}),
                ("Onion Powder", "Spices & Herbs", "teaspoons", {"calories": 8, "protein": 0, "carbs": 2, "fat": 0}),
                ("Chili Powder", "Spices & Herbs", "teaspoons", {"calories": 8, "protein": 0, "carbs": 1, "fat": 0}),
                ("Cayenne Pepper", "Spices & Herbs", "teaspoons", {"calories": 6, "protein": 0, "carbs": 1, "fat": 0}),
                
                # Oils & Condiments
                ("Olive Oil", "Oils & Condiments", "tablespoons", {"calories": 119, "protein": 0, "carbs": 0, "fat": 14}),
                ("Vegetable Oil", "Oils & Condiments", "tablespoons", {"calories": 120, "protein": 0, "carbs": 0, "fat": 14}),
                ("Canola Oil", "Oils & Condiments", "tablespoons", {"calories": 124, "protein": 0, "carbs": 0, "fat": 14}),
                ("Coconut Oil", "Oils & Condiments", "tablespoons", {"calories": 117, "protein": 0, "carbs": 0, "fat": 14}),
                ("Avocado Oil", "Oils & Condiments", "tablespoons", {"calories": 124, "protein": 0, "carbs": 0, "fat": 14}),
                ("Sesame Oil", "Oils & Condiments", "tablespoons", {"calories": 120, "protein": 0, "carbs": 0, "fat": 14}),
                ("Soy Sauce", "Oils & Condiments", "tablespoons", {"calories": 10, "protein": 2, "carbs": 1, "fat": 0}),
                ("Worcestershire Sauce", "Oils & Condiments", "tablespoons", {"calories": 11, "protein": 0, "carbs": 3, "fat": 0}),
                ("Hot Sauce", "Oils & Condiments", "tablespoons", {"calories": 1, "protein": 0, "carbs": 0, "fat": 0}),
                ("Ketchup", "Oils & Condiments", "tablespoons", {"calories": 19, "protein": 0, "carbs": 5, "fat": 0}),
                ("Mustard", "Oils & Condiments", "tablespoons", {"calories": 9, "protein": 1, "carbs": 1, "fat": 1}),
                ("Mayonnaise", "Oils & Condiments", "tablespoons", {"calories": 94, "protein": 0, "carbs": 0, "fat": 10}),
                ("Ranch Dressing", "Oils & Condiments", "tablespoons", {"calories": 73, "protein": 0, "carbs": 1, "fat": 8}),
                ("Balsamic Vinegar", "Oils & Condiments", "tablespoons", {"calories": 10, "protein": 0, "carbs": 2, "fat": 0}),
                ("Apple Cider Vinegar", "Oils & Condiments", "tablespoons", {"calories": 3, "protein": 0, "carbs": 0, "fat": 0}),
                ("White Vinegar", "Oils & Condiments", "tablespoons", {"calories": 3, "protein": 0, "carbs": 0, "fat": 0}),
                ("Honey", "Oils & Condiments", "tablespoons", {"calories": 64, "protein": 0, "carbs": 17, "fat": 0}),
                ("Maple Syrup", "Oils & Condiments", "tablespoons", {"calories": 52, "protein": 0, "carbs": 13, "fat": 0}),
                ("Lemon Juice", "Oils & Condiments", "tablespoons", {"calories": 4, "protein": 0, "carbs": 1, "fat": 0}),
                ("Lime Juice", "Oils & Condiments", "tablespoons", {"calories": 4, "protein": 0, "carbs": 1, "fat": 0}),
                
                # Nuts & Seeds
                ("Almonds", "Nuts & Seeds", "grams", {"calories": 579, "protein": 21, "carbs": 22, "fat": 50}),
                ("Walnuts", "Nuts & Seeds", "grams", {"calories": 654, "protein": 15, "carbs": 14, "fat": 65}),
                ("Cashews", "Nuts & Seeds", "grams", {"calories": 553, "protein": 18, "carbs": 30, "fat": 44}),
                ("Pecans", "Nuts & Seeds", "grams", {"calories": 691, "protein": 9, "carbs": 14, "fat": 72}),
                ("Brazil Nuts", "Nuts & Seeds", "grams", {"calories": 656, "protein": 14, "carbs": 12, "fat": 66}),
                ("Hazelnuts", "Nuts & Seeds", "grams", {"calories": 628, "protein": 15, "carbs": 17, "fat": 61}),
                ("Pistachios", "Nuts & Seeds", "grams", {"calories": 560, "protein": 20, "carbs": 28, "fat": 45}),
                ("Macadamia Nuts", "Nuts & Seeds", "grams", {"calories": 718, "protein": 8, "carbs": 14, "fat": 76}),
                ("Pine Nuts", "Nuts & Seeds", "grams", {"calories": 673, "protein": 14, "carbs": 13, "fat": 68}),
                ("Peanuts", "Nuts & Seeds", "grams", {"calories": 567, "protein": 26, "carbs": 16, "fat": 49}),
                ("Peanut Butter", "Nuts & Seeds", "tablespoons", {"calories": 94, "protein": 4, "carbs": 4, "fat": 8}),
                ("Almond Butter", "Nuts & Seeds", "tablespoons", {"calories": 98, "protein": 4, "carbs": 4, "fat": 9}),
                ("Sunflower Seeds", "Nuts & Seeds", "grams", {"calories": 584, "protein": 21, "carbs": 20, "fat": 51}),
                ("Pumpkin Seeds", "Nuts & Seeds", "grams", {"calories": 559, "protein": 30, "carbs": 11, "fat": 49}),
                ("Chia Seeds", "Nuts & Seeds", "tablespoons", {"calories": 58, "protein": 2, "carbs": 5, "fat": 4}),
                ("Flax Seeds", "Nuts & Seeds", "tablespoons", {"calories": 55, "protein": 2, "carbs": 3, "fat": 4}),
                ("Hemp Seeds", "Nuts & Seeds", "tablespoons", {"calories": 51, "protein": 3, "carbs": 1, "fat": 4}),
                ("Sesame Seeds", "Nuts & Seeds", "tablespoons", {"calories": 52, "protein": 2, "carbs": 2, "fat": 4}),
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