"""
Tests for Shopping List Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.shopping_list_service import ShoppingListService
from app.models.shopping import ShoppingList, ShoppingListItem
from app.models.meal_plan import MealPlan
from app.models.recipe_v2 import RecipeV2
from app.models.pantry import PantryItem
from app.models.ingredient import Ingredient
from app.schemas.shopping import GenerateShoppingListRequest


class TestShoppingListService:
    """Test cases for ShoppingListService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a shopping list service instance"""
        return ShoppingListService(mock_db)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return "test-user-123"
    
    @pytest.fixture
    def sample_meal_plans(self):
        """Create sample meal plans for testing"""
        recipe1 = RecipeV2(
            id="recipe-1",
            name="Chicken Stir Fry",
            servings=4,
            ingredients_needed=[
                {"name": "chicken breast", "quantity": 2, "unit": "lbs"},
                {"name": "bell pepper", "quantity": 3, "unit": "pieces"},
                {"name": "soy sauce", "quantity": 4, "unit": "tbsp"},
                {"name": "rice", "quantity": 2, "unit": "cups"}
            ]
        )
        
        recipe2 = RecipeV2(
            id="recipe-2",
            name="Pasta Carbonara",
            servings=4,
            ingredients_needed=[
                {"name": "pasta", "quantity": 1, "unit": "lb"},
                {"name": "bacon", "quantity": 8, "unit": "oz"},
                {"name": "eggs", "quantity": 4, "unit": "pieces"},
                {"name": "parmesan cheese", "quantity": 1, "unit": "cup"}
            ]
        )
        
        meal_plan1 = MealPlan(
            id="meal-plan-1",
            user_id="test-user-123",
            recipe_id="recipe-1",
            recipe=recipe1,
            date=datetime.now(),
            servings=4
        )
        
        meal_plan2 = MealPlan(
            id="meal-plan-2",
            user_id="test-user-123",
            recipe_id="recipe-2",
            recipe=recipe2,
            date=datetime.now() + timedelta(days=2),
            servings=6  # Different serving size
        )
        
        return [meal_plan1, meal_plan2]
    
    def test_generate_from_meal_plans_success(self, service, mock_db, sample_user_id, sample_meal_plans):
        """Test successful shopping list generation from meal plans"""
        # Setup request
        request = GenerateShoppingListRequest(
            week_start=datetime.now(),
            include_pantry_check=False
        )
        
        # Mock meal plan query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_meal_plans
        mock_db.query.return_value = mock_query
        
        # Mock recipe queries
        def query_side_effect(model):
            if model == MealPlan:
                return mock_query
            elif model == RecipeV2:
                recipe_query = Mock()
                recipe_query.filter.return_value = recipe_query
                if "recipe-1" in str(recipe_query.filter.call_args):
                    recipe_query.first.return_value = sample_meal_plans[0].recipe
                else:
                    recipe_query.first.return_value = sample_meal_plans[1].recipe
                return recipe_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Execute
        result = service.generate_from_meal_plans(sample_user_id, request)
        
        # Verify shopping list created
        assert mock_db.add.called
        assert mock_db.commit.called
        shopping_list_call = mock_db.add.call_args_list[0][0][0]
        assert isinstance(shopping_list_call, ShoppingList)
        assert shopping_list_call.user_id == sample_user_id
        assert shopping_list_call.week_start == request.week_start
        
        # Verify items created (should aggregate ingredients)
        item_calls = [call[0][0] for call in mock_db.add.call_args_list[1:] 
                      if isinstance(call[0][0], ShoppingListItem)]
        assert len(item_calls) > 0
        
        # Check specific items
        item_names = [item.name for item in item_calls]
        assert "chicken breast" in item_names
        assert "pasta" in item_names
        
    def test_generate_with_pantry_check(self, service, mock_db, sample_user_id, sample_meal_plans):
        """Test shopping list generation with pantry inventory check"""
        # Setup request with pantry check
        request = GenerateShoppingListRequest(
            week_start=datetime.now(),
            include_pantry_check=True
        )
        
        # Mock meal plans
        mock_meal_query = Mock()
        mock_meal_query.filter.return_value = mock_meal_query
        mock_meal_query.all.return_value = sample_meal_plans
        
        # Mock pantry items
        ingredient = Ingredient(name="rice")
        pantry_item = PantryItem(
            user_id=sample_user_id,
            ingredient=ingredient,
            quantity=5,  # Have 5 cups
            unit="cups"
        )
        
        mock_pantry_query = Mock()
        mock_pantry_query.filter.return_value = mock_pantry_query
        mock_pantry_query.all.return_value = [pantry_item]
        
        # Setup query routing
        def query_router(model):
            if model == MealPlan:
                return mock_meal_query
            elif model == PantryItem:
                return mock_pantry_query
            elif model == RecipeV2:
                recipe_query = Mock()
                recipe_query.filter.return_value = recipe_query
                recipe_query.first.return_value = sample_meal_plans[0].recipe
                return recipe_query
            return Mock()
        
        mock_db.query.side_effect = query_router
        
        # Execute
        result = service.generate_from_meal_plans(sample_user_id, request)
        
        # Verify pantry check was performed
        assert mock_db.query.call_count >= 2  # At least meal plans and pantry queries
        
        # Verify rice quantity was reduced (need 2 cups, have 5)
        item_calls = [call[0][0] for call in mock_db.add.call_args_list 
                      if isinstance(call[0][0], ShoppingListItem)]
        rice_items = [item for item in item_calls if item.name == "rice"]
        
        # Should either not add rice or add 0 quantity
        assert len(rice_items) == 0 or rice_items[0].quantity == 0
    
    def test_aggregate_ingredients_with_servings_multiplier(self, service, sample_meal_plans):
        """Test ingredient aggregation with different serving sizes"""
        # The second meal plan has 6 servings for a 4-serving recipe
        result = service._aggregate_ingredients_from_meal_plans(sample_meal_plans)
        
        # Check pasta quantity was scaled up (1 lb * 6/4 = 1.5 lbs)
        assert "pasta" in result
        assert result["pasta"]["quantity"] == 1.5
        assert result["pasta"]["unit"] == "lb"
        
        # Check source tracking
        assert "Pasta Carbonara" in result["pasta"]["source_recipes"]
        assert "meal-plan-2" in result["pasta"]["meal_plan_ids"]
    
    def test_normalize_ingredient_name(self, service):
        """Test ingredient name normalization"""
        # Test modifier removal
        assert service._normalize_ingredient_name("fresh tomatoes") == "tomato"
        assert service._normalize_ingredient_name("frozen chicken breast") == "chicken breast"
        assert service._normalize_ingredient_name("organic whole milk") == "milk"
        
        # Test plural handling
        assert service._normalize_ingredient_name("tomatoes") == "tomato"
        assert service._normalize_ingredient_name("berries") == "berry"
        assert service._normalize_ingredient_name("potatoes") == "potato"
        
        # Test case normalization
        assert service._normalize_ingredient_name("CHICKEN BREAST") == "chicken breast"
        assert service._normalize_ingredient_name("  Bell Pepper  ") == "bell pepper"
    
    def test_get_ingredient_category(self, service):
        """Test ingredient categorization"""
        # Test produce
        assert service._get_ingredient_category("tomato") == "produce"
        assert service._get_ingredient_category("bell pepper") == "produce"
        assert service._get_ingredient_category("fresh spinach") == "produce"
        
        # Test dairy
        assert service._get_ingredient_category("milk") == "dairy"
        assert service._get_ingredient_category("cheddar cheese") == "dairy"
        
        # Test meat
        assert service._get_ingredient_category("chicken breast") == "meat"
        assert service._get_ingredient_category("ground beef") == "meat"
        
        # Test pantry
        assert service._get_ingredient_category("rice") == "pantry"
        assert service._get_ingredient_category("pasta") == "pantry"
        
        # Test unknown
        assert service._get_ingredient_category("mystery ingredient") == "other"
    
    def test_estimate_ingredient_cost(self, service):
        """Test ingredient cost estimation"""
        # Test produce (base: $2.50)
        cost = service._estimate_ingredient_cost("tomato", 2, "lbs")
        assert cost > 0
        assert cost <= 7.50  # Max 3x multiplier
        
        # Test meat (base: $8.00)
        cost = service._estimate_ingredient_cost("chicken", 1, "lb")
        assert cost > 0
        assert cost <= 24.00  # Max 3x multiplier
        
        # Test quantity scaling
        small_cost = service._estimate_ingredient_cost("rice", 0.5, "cup")
        large_cost = service._estimate_ingredient_cost("rice", 10, "cups")
        assert large_cost > small_cost
    
    def test_units_compatible(self, service):
        """Test unit compatibility checking"""
        # Same units
        assert service._units_compatible("cup", "cup")
        assert service._units_compatible("lbs", "lbs")
        
        # Compatible weight units
        assert service._units_compatible("lb", "pounds")
        assert service._units_compatible("oz", "ounces")
        assert service._units_compatible("g", "grams")
        
        # Compatible volume units
        assert service._units_compatible("cup", "cups")
        assert service._units_compatible("tbsp", "tablespoon")
        assert service._units_compatible("ml", "l")
        
        # Compatible count units
        assert service._units_compatible("piece", "pieces")
        assert service._units_compatible("each", "whole")
        
        # Incompatible units
        assert not service._units_compatible("cup", "lb")
        assert not service._units_compatible("pieces", "ml")
        
        # Empty units (assume compatible)
        assert service._units_compatible("", "cup")
        assert service._units_compatible("lb", "")
    
    def test_add_manual_item(self, service, mock_db, sample_user_id):
        """Test adding manual items to shopping list"""
        # Setup shopping list
        shopping_list = ShoppingList(
            id="list-1",
            user_id=sample_user_id,
            name="Test List",
            total_items=5,
            estimated_total_cost=25.00
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = shopping_list
        mock_db.query.return_value = mock_query
        
        # Add manual item
        item_data = {
            "name": "Paper Towels",
            "quantity": 2,
            "unit": "rolls",
            "category": "household",
            "priority": "high",
            "notes": "Extra absorbent",
            "estimated_cost": 12.99
        }
        
        result = service.add_manual_item("list-1", sample_user_id, item_data)
        
        # Verify item added
        assert mock_db.add.called
        added_item = mock_db.add.call_args[0][0]
        assert isinstance(added_item, ShoppingListItem)
        assert added_item.name == "Paper Towels"
        assert added_item.quantity == 2
        assert added_item.manually_added is True
        assert added_item.priority == "high"
        
        # Verify list totals updated
        assert shopping_list.total_items == 6
        assert shopping_list.estimated_total_cost == 37.99
    
    def test_add_manual_item_unauthorized(self, service, mock_db):
        """Test adding item to unauthorized shopping list"""
        # Mock no shopping list found
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Attempt to add item
        with pytest.raises(ValueError, match="Shopping list not found"):
            service.add_manual_item("list-1", "wrong-user", {"name": "item"})
    
    def test_toggle_item_completion(self, service, mock_db, sample_user_id):
        """Test toggling item completion status"""
        # Setup shopping list and item
        shopping_list = ShoppingList(
            id="list-1",
            user_id=sample_user_id,
            completed_items=2,
            total_items=10
        )
        
        item = ShoppingListItem(
            id="item-1",
            shopping_list_id="list-1",
            shopping_list=shopping_list,
            name="Milk",
            is_completed=False,
            completed_at=None
        )
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = item
        mock_db.query.return_value = mock_query
        
        # Toggle to completed
        result = service.toggle_item_completion("item-1", sample_user_id)
        
        assert item.is_completed is True
        assert item.completed_at is not None
        assert shopping_list.completed_items == 3
        
        # Toggle back to uncompleted
        item.is_completed = True
        item.completed_at = datetime.utcnow()
        shopping_list.completed_items = 3
        
        result = service.toggle_item_completion("item-1", sample_user_id)
        
        assert item.is_completed is False
        assert item.completed_at is None
        assert shopping_list.completed_items == 2
    
    def test_bulk_toggle_items(self, service, mock_db, sample_user_id):
        """Test bulk toggling multiple items"""
        # Setup shopping list
        shopping_list = ShoppingList(
            id="list-1",
            user_id=sample_user_id,
            completed_items=1,
            total_items=5
        )
        
        # Create items with different states
        items = [
            ShoppingListItem(
                id=f"item-{i}",
                shopping_list_id="list-1",
                shopping_list=shopping_list,
                is_completed=(i == 0),  # First item already completed
                completed_at=datetime.utcnow() if i == 0 else None
            )
            for i in range(3)
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = items
        mock_db.query.return_value = mock_query
        
        # Mark all as completed
        item_ids = ["item-0", "item-1", "item-2"]
        count = service.bulk_toggle_items(item_ids, sample_user_id, completed=True)
        
        # Only 2 items should be updated (item-0 was already completed)
        assert count == 2
        assert all(item.is_completed for item in items)
        assert shopping_list.completed_items == 3
        
        # Mark all as uncompleted
        for item in items:
            item.is_completed = True
        shopping_list.completed_items = 3
        
        count = service.bulk_toggle_items(item_ids, sample_user_id, completed=False)
        
        assert count == 3
        assert not any(item.is_completed for item in items)
        assert shopping_list.completed_items == 0
    
    def test_generate_with_specific_meal_plan_ids(self, service, mock_db, sample_user_id, sample_meal_plans):
        """Test generating shopping list for specific meal plan IDs"""
        request = GenerateShoppingListRequest(
            week_start=datetime.now(),
            meal_plan_ids=["meal-plan-1"],  # Only first meal plan
            name="Selected Meals Shopping"
        )
        
        # Mock query to return only first meal plan
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_meal_plans[0]]
        mock_db.query.return_value = mock_query
        
        result = service.generate_from_meal_plans(sample_user_id, request)
        
        # Verify meal plan ID filter was applied
        assert mock_db.query.called
        
        # Should only have ingredients from first recipe
        item_calls = [call[0][0] for call in mock_db.add.call_args_list 
                      if isinstance(call[0][0], ShoppingListItem)]
        item_names = [item.name for item in item_calls]
        
        # Should have chicken stir fry ingredients
        assert any("chicken" in name for name in item_names)
        assert any("pepper" in name for name in item_names)
        
        # Should NOT have pasta carbonara ingredients
        assert not any("pasta" in name for name in item_names)
        assert not any("bacon" in name for name in item_names)
    
    def test_error_handling_and_rollback(self, service, mock_db, sample_user_id):
        """Test error handling and database rollback"""
        request = GenerateShoppingListRequest(week_start=datetime.now())
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection error")
        
        # Execute and expect exception
        with pytest.raises(Exception, match="Database connection error"):
            service.generate_from_meal_plans(sample_user_id, request)
        
        # Verify rollback was called
        assert mock_db.rollback.called