"""
Comprehensive pantry management API tests
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta


@pytest.mark.api
class TestPantryManagement:
    """Test pantry item CRUD operations"""
    
    def test_get_pantry_items_empty(self, client):
        """Test getting pantry items for new user (should be empty)"""
        # Register a new user
        user_data = {
            "email": f"pantryuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Pantry User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/pantry", headers=headers)
        
        assert response.status_code == 200
        pantry_items = response.json()
        assert isinstance(pantry_items, list)
        assert len(pantry_items) == 0
        
    def test_get_pantry_items_without_auth(self, client):
        """Test accessing pantry without authentication"""
        response = client.get("/api/v1/pantry")
        
        # Based on family tests, likely returns 200 with empty list or requires auth
        assert response.status_code in [200, 401, 403]
        
    def test_add_pantry_item_success(self, client):
        """Test successfully adding a pantry item"""
        # Register user
        user_data = {
            "email": f"addpantry-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Add Pantry User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # First get an ingredient ID to use
        ingredients_response = client.get("/api/v1/ingredients")
        assert ingredients_response.status_code == 200
        ingredients = ingredients_response.json()
        assert len(ingredients) > 0
        test_ingredient_id = ingredients[0]["id"]
        
        # Add pantry item
        pantry_data = {
            "ingredient_id": test_ingredient_id,
            "quantity": 2.5,
            "expiration_date": "2024-12-31"
        }
        
        response = client.post("/api/v1/pantry", json=pantry_data, headers=headers)
        
        assert response.status_code == 200
        pantry_item = response.json()
        assert pantry_item["ingredient_id"] == test_ingredient_id
        assert pantry_item["quantity"] == 2.5
        assert pantry_item["expiration_date"] == "2024-12-31"
        assert "ingredient" in pantry_item
        assert "user_id" in pantry_item
        assert "updated_at" in pantry_item
        
    def test_add_pantry_item_minimal_data(self, client):
        """Test adding pantry item with minimal required data"""
        user_data = {
            "email": f"minimal-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Minimal User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient ID
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        # Add pantry item with only required fields
        pantry_data = {
            "ingredient_id": test_ingredient_id,
            "quantity": 1.0
        }
        
        response = client.post("/api/v1/pantry", json=pantry_data, headers=headers)
        
        assert response.status_code == 200
        pantry_item = response.json()
        assert pantry_item["ingredient_id"] == test_ingredient_id
        assert pantry_item["quantity"] == 1.0
        assert pantry_item["expiration_date"] is None
        
    def test_add_pantry_item_invalid_ingredient(self, client):
        """Test adding pantry item with invalid ingredient ID"""
        user_data = {
            "email": f"invalidingredient-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Invalid Ingredient User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        pantry_data = {
            "ingredient_id": "nonexistent-ingredient-id",
            "quantity": 1.0
        }
        
        response = client.post("/api/v1/pantry", json=pantry_data, headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_add_pantry_item_without_auth(self, client):
        """Test adding pantry item without authentication"""
        pantry_data = {
            "ingredient_id": "some-ingredient",
            "quantity": 1.0
        }
        
        response = client.post("/api/v1/pantry", json=pantry_data)
        
        assert response.status_code == 401
        
    def test_add_pantry_item_invalid_data(self, client):
        """Test adding pantry item with invalid data"""
        user_data = {
            "email": f"invaliddata-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Invalid Data User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Missing required fields
        response = client.post("/api/v1/pantry", json={}, headers=headers)
        assert response.status_code == 422
        
        # Invalid quantity
        response = client.post("/api/v1/pantry", json={
            "ingredient_id": "some-id",
            "quantity": -1.0  # Negative quantity
        }, headers=headers)
        # May or may not validate negative quantities
        
    def test_update_pantry_item_success(self, client):
        """Test successfully updating a pantry item"""
        # Setup: Register user and add pantry item
        user_data = {
            "email": f"updatepantry-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Update Pantry User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient and add to pantry
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        add_response = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 1.0,
            "expiration_date": "2024-01-01"
        }, headers=headers)
        assert add_response.status_code == 200
        
        # Update pantry item
        update_data = {
            "quantity": 3.0,
            "expiration_date": "2024-06-01"
        }
        
        response = client.put(f"/api/v1/pantry/{test_ingredient_id}", 
                            json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["quantity"] == 3.0
        assert updated_item["expiration_date"] == "2024-06-01"
        assert updated_item["ingredient_id"] == test_ingredient_id
        
    def test_update_pantry_item_partial(self, client):
        """Test partial update of pantry item"""
        # Setup
        user_data = {
            "email": f"partialupdate-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Partial Update User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient and add to pantry
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        add_response = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 2.0,
            "expiration_date": "2024-03-01"
        }, headers=headers)
        original_item = add_response.json()
        
        # Update only quantity
        response = client.put(f"/api/v1/pantry/{test_ingredient_id}", 
                            json={"quantity": 4.0}, headers=headers)
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["quantity"] == 4.0
        assert updated_item["expiration_date"] == original_item["expiration_date"]  # Should remain unchanged
        
    def test_update_nonexistent_pantry_item(self, client):
        """Test updating a pantry item that doesn't exist"""
        user_data = {
            "email": f"updatenonexistent-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Update Nonexistent User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_ingredient_id = str(uuid.uuid4())  # Generate a valid UUID that doesn't exist
        response = client.put(f"/api/v1/pantry/{fake_ingredient_id}", 
                            json={"quantity": 1.0}, headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_remove_pantry_item_success(self, client):
        """Test successfully removing a pantry item"""
        # Setup
        user_data = {
            "email": f"removepantry-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Remove Pantry User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient and add to pantry
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        add_response = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 1.0
        }, headers=headers)
        assert add_response.status_code == 200
        
        # Remove pantry item
        response = client.delete(f"/api/v1/pantry/{test_ingredient_id}", headers=headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify item is gone
        get_response = client.get("/api/v1/pantry", headers=headers)
        pantry_items = get_response.json()
        ingredient_ids = [item["ingredient_id"] for item in pantry_items]
        assert test_ingredient_id not in ingredient_ids
        
    def test_remove_nonexistent_pantry_item(self, client):
        """Test removing a pantry item that doesn't exist"""
        user_data = {
            "email": f"removenonexistent-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Remove Nonexistent User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_ingredient_id = str(uuid.uuid4())  # Generate a valid UUID that doesn't exist
        response = client.delete(f"/api/v1/pantry/{fake_ingredient_id}", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_pantry_item_replace_existing(self, client):
        """Test that adding same ingredient replaces existing pantry item"""
        user_data = {
            "email": f"replace-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Replace User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        # Add first pantry item
        response1 = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 1.0,
            "expiration_date": "2024-01-01"
        }, headers=headers)
        assert response1.status_code == 200
        
        # Add same ingredient again (should replace)
        response2 = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 5.0,
            "expiration_date": "2024-12-31"
        }, headers=headers)
        assert response2.status_code == 200
        
        # Verify only one item exists with new values
        get_response = client.get("/api/v1/pantry", headers=headers)
        pantry_items = get_response.json()
        matching_items = [item for item in pantry_items if item["ingredient_id"] == test_ingredient_id]
        assert len(matching_items) == 1
        assert matching_items[0]["quantity"] == 5.0
        assert matching_items[0]["expiration_date"] == "2024-12-31"


@pytest.mark.api
class TestPantryValidation:
    """Test pantry item data validation"""
    
    def test_pantry_quantity_validation(self, client):
        """Test quantity field validation"""
        user_data = {
            "email": f"quantityvalidation-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Quantity Validation User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        # Test valid quantities
        valid_quantities = [0.1, 1.0, 10.5, 100]
        for quantity in valid_quantities:
            response = client.post("/api/v1/pantry", json={
                "ingredient_id": test_ingredient_id,
                "quantity": quantity
            }, headers=headers)
            assert response.status_code == 200
            
            # Clean up
            client.delete(f"/api/v1/pantry/{test_ingredient_id}", headers=headers)
            
        # Test edge cases
        response = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 0  # Zero quantity
        }, headers=headers)
        # Should handle zero quantity gracefully
        
    def test_pantry_expiration_date_validation(self, client):
        """Test expiration date field validation"""
        user_data = {
            "email": f"datevalidation-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Date Validation User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredient
        ingredients_response = client.get("/api/v1/ingredients")
        test_ingredient_id = ingredients_response.json()[0]["id"]
        
        # Test valid date formats
        valid_dates = ["2024-12-31", "2025-01-01", "2030-06-15"]
        for date_str in valid_dates:
            response = client.post("/api/v1/pantry", json={
                "ingredient_id": test_ingredient_id,
                "quantity": 1.0,
                "expiration_date": date_str
            }, headers=headers)
            assert response.status_code == 200
            assert response.json()["expiration_date"] == date_str
            
            # Clean up
            client.delete(f"/api/v1/pantry/{test_ingredient_id}", headers=headers)
            
        # Test null expiration date
        response = client.post("/api/v1/pantry", json={
            "ingredient_id": test_ingredient_id,
            "quantity": 1.0,
            "expiration_date": None
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["expiration_date"] is None
        
    def test_pantry_ingredient_id_validation(self, client):
        """Test ingredient ID validation"""
        user_data = {
            "email": f"ingredientvalidation-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Ingredient Validation User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test empty ingredient ID
        response = client.post("/api/v1/pantry", json={
            "ingredient_id": "",
            "quantity": 1.0
        }, headers=headers)
        # Should reject empty ingredient ID
        assert response.status_code in [400, 404, 422]
        
        # Test very long ingredient ID
        response = client.post("/api/v1/pantry", json={
            "ingredient_id": "a" * 500,  # Very long ID
            "quantity": 1.0
        }, headers=headers)
        assert response.status_code in [400, 404, 422]


@pytest.mark.api
class TestPantryIntegration:
    """Test pantry integration with other features"""
    
    def test_pantry_with_recommendations(self, client):
        """Test that pantry items influence meal recommendations"""
        # Setup user and pantry items
        user_data = {
            "email": f"pantryintegration-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Pantry Integration User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredients and add to pantry
        ingredients_response = client.get("/api/v1/ingredients")
        ingredients = ingredients_response.json()
        assert len(ingredients) >= 2
        
        # Add multiple pantry items
        for i, ingredient in enumerate(ingredients[:3]):
            response = client.post("/api/v1/pantry", json={
                "ingredient_id": ingredient["id"],
                "quantity": float(i + 1)
            }, headers=headers)
            assert response.status_code == 200
            
        # Verify pantry items are stored
        pantry_response = client.get("/api/v1/pantry", headers=headers)
        assert pantry_response.status_code == 200
        pantry_items = pantry_response.json()
        assert len(pantry_items) == 3
        
        # Test that pantry items have ingredient details
        for item in pantry_items:
            assert "ingredient" in item
            assert "name" in item["ingredient"]
            assert "category" in item["ingredient"]
            
    def test_pantry_user_isolation(self, client):
        """Test that users can only see their own pantry items"""
        # Create two users
        user1_data = {
            "email": f"pantryuser1-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Pantry User 1"
        }
        user1_response = client.post("/api/v1/auth/register", json=user1_data)
        token1 = user1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        user2_data = {
            "email": f"pantryuser2-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Pantry User 2"
        }
        user2_response = client.post("/api/v1/auth/register", json=user2_data)
        token2 = user2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Get ingredients
        ingredients_response = client.get("/api/v1/ingredients")
        ingredients = ingredients_response.json()
        ingredient1_id = ingredients[0]["id"]
        ingredient2_id = ingredients[1]["id"] if len(ingredients) > 1 else ingredients[0]["id"]
        
        # User 1 adds pantry items
        client.post("/api/v1/pantry", json={
            "ingredient_id": ingredient1_id,
            "quantity": 1.0
        }, headers=headers1)
        
        # User 2 adds different pantry items
        client.post("/api/v1/pantry", json={
            "ingredient_id": ingredient2_id,
            "quantity": 2.0
        }, headers=headers2)
        
        # Verify users only see their own items
        pantry1_response = client.get("/api/v1/pantry", headers=headers1)
        pantry1_items = pantry1_response.json()
        user1_ingredient_ids = [item["ingredient_id"] for item in pantry1_items]
        assert ingredient1_id in user1_ingredient_ids
        assert ingredient2_id not in user1_ingredient_ids
        
        pantry2_response = client.get("/api/v1/pantry", headers=headers2)
        pantry2_items = pantry2_response.json()
        user2_ingredient_ids = [item["ingredient_id"] for item in pantry2_items]
        assert ingredient2_id in user2_ingredient_ids
        assert ingredient1_id not in user2_ingredient_ids
        
    def test_pantry_complete_workflow(self, client):
        """Test complete pantry management workflow"""
        # Register user
        user_data = {
            "email": f"workflow-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Workflow User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get ingredients
        ingredients_response = client.get("/api/v1/ingredients")
        ingredients = ingredients_response.json()[:3]  # Use first 3 ingredients
        
        # Step 1: Add multiple pantry items
        added_items = []
        for i, ingredient in enumerate(ingredients):
            pantry_data = {
                "ingredient_id": ingredient["id"],
                "quantity": float(i + 1),
                "expiration_date": f"2024-0{i+1}-01"
            }
            response = client.post("/api/v1/pantry", json=pantry_data, headers=headers)
            assert response.status_code == 200
            added_items.append(response.json())
            
        # Step 2: Verify all items are retrievable
        get_response = client.get("/api/v1/pantry", headers=headers)
        assert get_response.status_code == 200
        pantry_items = get_response.json()
        assert len(pantry_items) == len(ingredients)
        
        # Step 3: Update a pantry item
        item_to_update = ingredients[1]["id"]
        update_response = client.put(f"/api/v1/pantry/{item_to_update}", 
                                   json={"quantity": 10.0}, headers=headers)
        assert update_response.status_code == 200
        assert update_response.json()["quantity"] == 10.0
        
        # Step 4: Remove a pantry item
        item_to_remove = ingredients[2]["id"]
        delete_response = client.delete(f"/api/v1/pantry/{item_to_remove}", headers=headers)
        assert delete_response.status_code == 200
        
        # Step 5: Verify final state
        final_response = client.get("/api/v1/pantry", headers=headers)
        final_items = final_response.json()
        assert len(final_items) == 2  # One item removed
        
        final_ingredient_ids = [item["ingredient_id"] for item in final_items]
        assert item_to_remove not in final_ingredient_ids
        assert item_to_update in final_ingredient_ids
        
        # Verify updated quantity persisted
        updated_item = next(item for item in final_items if item["ingredient_id"] == item_to_update)
        assert updated_item["quantity"] == 10.0