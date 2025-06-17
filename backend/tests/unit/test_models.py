import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.simple_user import User
from app.models.ingredient import Ingredient, IngredientCategory, PantryItem


@pytest.mark.unit
class TestUserModel:
    """Test the User model"""
    
    def test_user_creation(self, db_session):
        """Test creating a user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_123",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.timezone == "UTC"  # default value
        assert user.is_active is True  # default value
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_unique_email_constraint(self, db_session):
        """Test that email must be unique"""
        user1 = User(
            email="duplicate@example.com",
            hashed_password="password1",
            name="User 1"
        )
        user2 = User(
            email="duplicate@example.com",
            hashed_password="password2",
            name="User 2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_id_generation(self, db_session):
        """Test that user ID is automatically generated as UUID"""
        user = User(
            email="uuid_test@example.com",
            hashed_password="password",
            name="UUID Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Should be a valid UUID string
        assert user.id is not None
        uuid.UUID(user.id)  # This will raise ValueError if not valid UUID
    
    def test_user_optional_fields(self, db_session):
        """Test user creation with minimal required fields"""
        user = User(
            email="minimal@example.com",
            hashed_password="password"
            # name is optional
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "minimal@example.com"
        assert user.name is None


@pytest.mark.unit
class TestIngredientModels:
    """Test the Ingredient-related models"""
    
    def test_ingredient_category_creation(self, db_session):
        """Test creating an ingredient category"""
        category = IngredientCategory(name="Proteins")
        
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "Proteins"
        assert category.parent_category_id is None
    
    def test_ingredient_category_hierarchy(self, db_session):
        """Test ingredient category parent-child relationship"""
        parent_category = IngredientCategory(name="Proteins")
        db_session.add(parent_category)
        db_session.commit()
        
        child_category = IngredientCategory(
            name="Poultry",
            parent_category_id=parent_category.id
        )
        db_session.add(child_category)
        db_session.commit()
        
        assert child_category.parent_category_id == parent_category.id
        assert child_category.parent_category.name == "Proteins"
    
    def test_ingredient_creation(self, db_session):
        """Test creating an ingredient"""
        category = IngredientCategory(name="Proteins")
        db_session.add(category)
        db_session.commit()
        
        ingredient = Ingredient(
            name="Chicken Breast",
            category_id=category.id,
            unit="grams",
            nutritional_info={"protein": 23, "calories": 165},
            allergens=[]
        )
        
        db_session.add(ingredient)
        db_session.commit()
        
        assert ingredient.id is not None
        assert ingredient.name == "Chicken Breast"
        assert ingredient.unit == "grams"
        assert ingredient.nutritional_info["protein"] == 23
        assert ingredient.allergens == []
        assert ingredient.category.name == "Proteins"
    
    def test_ingredient_unique_name_constraint(self, db_session):
        """Test that ingredient names must be unique"""
        category = IngredientCategory(name="Test Category")
        db_session.add(category)
        db_session.commit()
        
        ingredient1 = Ingredient(
            name="Duplicate Name",
            category_id=category.id,
            unit="grams"
        )
        ingredient2 = Ingredient(
            name="Duplicate Name",
            category_id=category.id,
            unit="pieces"
        )
        
        db_session.add(ingredient1)
        db_session.commit()
        
        db_session.add(ingredient2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_ingredient_default_values(self, db_session):
        """Test ingredient default values"""
        category = IngredientCategory(name="Test Category")
        db_session.add(category)
        db_session.commit()
        
        ingredient = Ingredient(
            name="Test Ingredient",
            category_id=category.id,
            unit="grams"
            # nutritional_info and allergens should use defaults
        )
        
        db_session.add(ingredient)
        db_session.commit()
        
        assert ingredient.nutritional_info == {}
        assert ingredient.allergens == []


@pytest.mark.unit
class TestPantryItemModel:
    """Test the PantryItem model"""
    
    def test_pantry_item_creation(self, db_session):
        """Test creating a pantry item"""
        # Create dependencies
        user = User(
            email="pantry_test@example.com",
            hashed_password="password",
            name="Pantry Test User"
        )
        category = IngredientCategory(name="Test Category")
        ingredient = Ingredient(
            name="Test Ingredient",
            category_id=None,  # Will set after category is committed
            unit="grams"
        )
        
        db_session.add(user)
        db_session.add(category)
        db_session.commit()
        
        ingredient.category_id = category.id
        db_session.add(ingredient)
        db_session.commit()
        
        pantry_item = PantryItem(
            user_id=uuid.UUID(user.id),
            ingredient_id=ingredient.id,
            quantity=250.0,
            expiration_date=datetime(2024, 12, 31)
        )
        
        db_session.add(pantry_item)
        db_session.commit()
        
        assert pantry_item.user_id == uuid.UUID(user.id)
        assert pantry_item.ingredient_id == ingredient.id
        assert pantry_item.quantity == 250.0
        assert pantry_item.expiration_date.year == 2024
        assert pantry_item.updated_at is not None
    
    def test_pantry_item_default_quantity(self, db_session):
        """Test pantry item default quantity"""
        # Create dependencies
        user = User(
            email="pantry_default@example.com",
            hashed_password="password"
        )
        category = IngredientCategory(name="Test Category")
        ingredient = Ingredient(
            name="Default Test Ingredient",
            category_id=None,
            unit="grams"
        )
        
        db_session.add(user)
        db_session.add(category)
        db_session.commit()
        
        ingredient.category_id = category.id
        db_session.add(ingredient)
        db_session.commit()
        
        pantry_item = PantryItem(
            user_id=uuid.UUID(user.id),
            ingredient_id=ingredient.id
            # quantity should default to 0
        )
        
        db_session.add(pantry_item)
        db_session.commit()
        
        assert pantry_item.quantity == 0.0
    
    def test_pantry_item_composite_primary_key(self, db_session):
        """Test that pantry items have composite primary key (user_id, ingredient_id)"""
        # Create dependencies
        user = User(
            email="composite_test@example.com",
            hashed_password="password"
        )
        category = IngredientCategory(name="Test Category")
        ingredient = Ingredient(
            name="Composite Test Ingredient",
            category_id=None,
            unit="grams"
        )
        
        db_session.add(user)
        db_session.add(category)
        db_session.commit()
        
        ingredient.category_id = category.id
        db_session.add(ingredient)
        db_session.commit()
        
        # First pantry item
        pantry_item1 = PantryItem(
            user_id=uuid.UUID(user.id),
            ingredient_id=ingredient.id,
            quantity=100.0
        )
        
        db_session.add(pantry_item1)
        db_session.commit()
        
        # Try to add another pantry item with same user_id and ingredient_id
        pantry_item2 = PantryItem(
            user_id=uuid.UUID(user.id),
            ingredient_id=ingredient.id,
            quantity=200.0
        )
        
        db_session.add(pantry_item2)
        with pytest.raises(IntegrityError):
            db_session.commit()