"""
Test recipe API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import uuid
from datetime import datetime

from app.main import create_app
from app.models.recipe_v2 import RecipeV2
from app.models.recipe_rating import RecipeRating
from app.api.recipes import get_current_user_simple
from app.db.database import get_db

# Create test app
app = create_app()
client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for tests"""
    return {
        "name": "Test Recipe",
        "description": "A delicious test recipe",
        "prep_time": 30,
        "difficulty": "Medium",
        "servings": 4,
        "ingredients_needed": [
            {"name": "Ingredient 1", "quantity": "2", "unit": "cups", "have_in_pantry": False},
            {"name": "Ingredient 2", "quantity": "1", "unit": "tbsp", "have_in_pantry": False}
        ],
        "instructions": ["Step 1: Do this", "Step 2: Do that"],
        "tags": ["test", "recipe"],
        "nutrition_notes": "Healthy and nutritious",
        "pantry_usage_score": 80,
        "source": "manual",
        "ai_generated": False
    }


class TestRecipesAPI:
    """Test recipes API endpoints"""
    
    @patch('app.api.recipes.get_db')
    def test_list_recipes_success(self, mock_get_db, mock_user):
        """Test successful listing of recipes"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock query results
        mock_recipes = [
            RecipeV2(
                id=uuid.uuid4(),
                user_id=uuid.UUID(mock_user["id"]),
                name="Recipe 1",
                description="Description 1",
                prep_time=20,
                difficulty="Easy",
                servings=2,
                ingredients_needed=[],
                instructions=["Step 1"],
                tags=[],
                nutrition_notes="",
                pantry_usage_score=0,
                source="test",
                ai_generated=False,
                ai_provider=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            RecipeV2(
                id=uuid.uuid4(),
                user_id=uuid.UUID(mock_user["id"]),
                name="Recipe 2",
                description="Description 2",
                prep_time=45,
                difficulty="Hard",
                servings=6,
                ingredients_needed=[],
                instructions=["Step 1", "Step 2"],
                tags=[],
                nutrition_notes="",
                pantry_usage_score=0,
                source="test",
                ai_generated=False,
                ai_provider=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_recipes
        
        # Override dependencies for this test
        app.dependency_overrides[get_current_user_simple] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            # Make request
            response = client.get("/api/v1/recipes")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Recipe 1"
            assert data[1]["name"] == "Recipe 2"
        finally:
            # Clean up override
            app.dependency_overrides.clear()
    
    @patch('app.api.recipes.get_current_user_simple')
    def test_list_recipes_unauthorized(self, mock_get_user):
        """Test listing recipes without authentication"""
        mock_get_user.side_effect = Exception("Authentication required")
        
        response = client.get("/api/v1/recipes")
        assert response.status_code == 401
    
    @patch('app.api.recipes.get_db')
    def test_create_recipe_success(self, mock_get_db, mock_user, sample_recipe_data):
        """Test successful recipe creation"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Create a mock recipe object to return
        mock_recipe = RecipeV2(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            name=sample_recipe_data["name"],
            description=sample_recipe_data["description"],
            prep_time=sample_recipe_data["prep_time"],
            difficulty=sample_recipe_data["difficulty"],
            servings=sample_recipe_data["servings"],
            ingredients_needed=sample_recipe_data["ingredients_needed"],
            instructions=sample_recipe_data["instructions"],
            tags=[],
            nutrition_notes="",
            pantry_usage_score=0,
            source="test",
            ai_generated=False,
            ai_provider=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock database interactions
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Override dependencies for this test
        app.dependency_overrides[get_current_user_simple] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            # Mock the refresh to set the recipe properties
            def mock_refresh(obj):
                obj.id = mock_recipe.id
                obj.created_at = mock_recipe.created_at
                obj.updated_at = mock_recipe.updated_at
            mock_db.refresh.side_effect = mock_refresh
            
            # Make request
            response = client.post("/api/v1/recipes", json=sample_recipe_data)
            
            # Debug output if test fails
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == sample_recipe_data["name"]
            assert data["description"] == sample_recipe_data["description"]
            assert data["user_id"] == mock_user["id"]
            assert mock_db.add.called
        finally:
            # Clean up override
            app.dependency_overrides.clear()
        assert mock_db.commit.called
    
    @patch('app.api.recipes.get_db')
    def test_rate_recipe_success(self, mock_get_db, mock_user):
        """Test successful recipe rating"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        recipe_id = str(uuid.uuid4())
        mock_recipe = RecipeV2(
            id=uuid.UUID(recipe_id),
            user_id=uuid.uuid4(),
            name="Test Recipe",
            description="Test",
            prep_time=30,
            difficulty="Medium",
            servings=4,
            ingredients_needed=[],
            instructions=["Step 1"],
            tags=[],
            nutrition_notes="",
            pantry_usage_score=0,
            source="test",
            ai_generated=False,
            ai_provider=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock recipe exists
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recipe
        
        # Mock no existing rating
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_recipe, None]
        
        rating_data = {
            "rating": 5,
            "review_text": "Excellent recipe!",
            "would_make_again": True,
            "cooking_notes": "Added extra spice"
        }
        
        # Create mock rating to return after save
        mock_rating = RecipeRating(
            id=uuid.uuid4(),
            recipe_id=uuid.UUID(recipe_id),
            user_id=uuid.UUID(mock_user["id"]),
            rating=5,
            review_text="Excellent recipe!",
            would_make_again=True,
            cooking_notes="Added extra spice",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock the refresh to set the rating properties
        def mock_refresh(obj):
            obj.id = mock_rating.id
            obj.created_at = mock_rating.created_at
            obj.updated_at = mock_rating.updated_at
        mock_db.refresh.side_effect = mock_refresh
        
        # Override dependencies for this test
        app.dependency_overrides[get_current_user_simple] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            # Make request
            response = client.post(f"/api/v1/recipes/{recipe_id}/ratings", json=rating_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["rating"] == 5
            assert data["review_text"] == "Excellent recipe!"
            assert data["would_make_again"] is True
            assert mock_db.add.called
            assert mock_db.commit.called
        finally:
            # Clean up override
            app.dependency_overrides.clear()
    
    @patch('app.api.recipes.get_db')
    def test_rate_recipe_already_rated(self, mock_get_db, mock_user):
        """Test rating a recipe that user already rated"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        recipe_id = str(uuid.uuid4())
        mock_recipe = RecipeV2(
            id=uuid.UUID(recipe_id),
            user_id=uuid.uuid4(),
            name="Test Recipe",
            description="Test",
            prep_time=30,
            difficulty="Medium",
            servings=4,
            ingredients_needed=[],
            instructions=["Step 1"],
            tags=[],
            nutrition_notes="",
            pantry_usage_score=0,
            source="test",
            ai_generated=False,
            ai_provider=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        existing_rating = RecipeRating(
            id=uuid.uuid4(),
            recipe_id=uuid.UUID(recipe_id),
            user_id=uuid.UUID(mock_user["id"]),
            rating=4,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock recipe exists and user already rated
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_recipe, existing_rating]
        
        rating_data = {
            "rating": 5,
            "review_text": "Even better!",
            "would_make_again": True
        }
        
        # Override dependencies for this test
        app.dependency_overrides[get_current_user_simple] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            # Make request
            response = client.post(f"/api/v1/recipes/{recipe_id}/ratings", json=rating_data)
            
            # Assertions
            assert response.status_code == 400
            assert "already rated" in response.json()["detail"]
        finally:
            # Clean up override
            app.dependency_overrides.clear()
    
    @patch('app.api.recipes.get_db')
    def test_health_check_success(self, mock_get_db, mock_user):
        """Test recipes health check endpoint"""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock recipe count
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        # Override dependencies for this test
        app.dependency_overrides[get_current_user_simple] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            # Make request
            response = client.get("/api/v1/recipes/debug/health")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "recipes_v2"
            assert data["user_id"] == mock_user["id"]
            assert data["user_recipe_count"] == 5
            assert data["database_connected"] is True
        finally:
            # Clean up override
            app.dependency_overrides.clear()