"""
Integration tests for Family and Pantry management
Tests the exact operations users perform before hitting recommendations/recipes
"""
import pytest
import json
from fastapi.testclient import TestClient

@pytest.fixture
def test_user_token(client):
    """Create a test user and return auth token"""
    import uuid
    user_data = {
        "email": f"familypantry-{uuid.uuid4()}@test.com",
        "password": "testpass123",
        "name": "Family Pantry Tester"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(test_user_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {test_user_token}"}


class TestFamilyManagement:
    """Test family member CRUD operations that happen before recommendations"""
    
    def test_add_family_member_with_complex_data(self, client, auth_headers):
        """Test adding family member with dietary restrictions and preferences"""
        family_data = {
            "name": "Alice Johnson",
            "age": 8,
            "dietary_restrictions": ["gluten-free", "dairy-free"],
            "preferences": {
                "likes": ["chicken", "rice", "vegetables"],
                "dislikes": ["fish", "spicy food"],
                "allergies": ["nuts"],
                "cooking_notes": "Prefers mild flavors"
            }
        }
        
        print(f"\n👨‍👩‍👧‍👦 Adding family member: {family_data}")
        response = client.post("/api/v1/family/members", json=family_data, headers=auth_headers)
        print(f"👨‍👩‍👧‍👦 Response status: {response.status_code}")
        print(f"👨‍👩‍👧‍👦 Response body: {response.text}")
        
        assert response.status_code == 200
        family_response = response.json()
        
        # Verify the data was stored correctly
        assert family_response["name"] == family_data["name"]
        assert family_response["age"] == family_data["age"]
        assert family_response["dietary_restrictions"] == family_data["dietary_restrictions"]
        assert family_response["preferences"] == family_data["preferences"]
        
        return family_response["id"]
    
    
    def test_get_family_members(self, client, auth_headers):
        """Test retrieving family members list"""
        # Add a family member first
        family_data = {
            "name": "Bob Smith",
            "age": 35,
            "dietary_restrictions": ["vegetarian"],
            "preferences": {"likes": ["pasta", "salads"]}
        }
        
        response = client.post("/api/v1/family/members", json=family_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Get the list
        print(f"\n👨‍👩‍👧‍👦 Getting family members list...")
        response = client.get("/api/v1/family/members", headers=auth_headers)
        print(f"👨‍👩‍👧‍👦 Get response status: {response.status_code}")
        print(f"👨‍👩‍👧‍👦 Get response body: {response.text}")
        
        assert response.status_code == 200
        family_list = response.json()
        assert len(family_list) > 0
        
        # Verify the family member is in the list
        found_member = None
        for member in family_list:
            if member["name"] == "Bob Smith":
                found_member = member
                break
        
        assert found_member is not None
        assert found_member["dietary_restrictions"] == ["vegetarian"]
    
    
    def test_family_member_data_types(self, client, auth_headers):
        """Test different data types in family member fields"""
        test_cases = [
            {
                "name": "Child with No Restrictions",
                "age": 5,
                "dietary_restrictions": [],
                "preferences": {}
            },
            {
                "name": "Adult with Multiple Restrictions",
                "age": 45,
                "dietary_restrictions": ["vegan", "gluten-free", "soy-free"],
                "preferences": {
                    "cuisines": ["mediterranean", "asian"],
                    "spice_level": "medium",
                    "cooking_methods": ["grilled", "steamed"]
                }
            },
            {
                "name": "Teen with String Preferences",
                "age": 16,
                "dietary_restrictions": ["lactose-intolerant"],
                "preferences": {
                    "favorite_meal": "dinner",
                    "notes": "Loves trying new foods"
                }
            }
        ]
        
        for case in test_cases:
            print(f"\n👨‍👩‍👧‍👦 Testing case: {case['name']}")
            response = client.post("/api/v1/family/members", json=case, headers=auth_headers)
            print(f"👨‍👩‍👧‍👦 Response: {response.status_code} - {response.text}")
            assert response.status_code == 200
            
            result = response.json()
            assert result["name"] == case["name"]
            assert result["dietary_restrictions"] == case["dietary_restrictions"]
            assert result["preferences"] == case["preferences"]


class TestPantryManagement:
    """Test pantry item operations that happen before recommendations"""
    
    def test_add_pantry_items_batch(self, client, auth_headers, test_ingredient_ids):
        """Test adding multiple pantry items like a real user would"""
        pantry_items = [
            {"ingredient_id": test_ingredient_ids['chicken_breast'], "quantity": 2.0, "expiration_date": "2024-12-31"},
            {"ingredient_id": test_ingredient_ids['rice'], "quantity": 5.0, "expiration_date": "2025-12-31"},
            {"ingredient_id": test_ingredient_ids['broccoli'], "quantity": 2.0, "expiration_date": "2024-12-25"}
        ]
        
        print(f"\n🥫 Adding {len(pantry_items)} pantry items...")
        added_items = []
        
        for i, item in enumerate(pantry_items):
            print(f"🥫 Adding item {i+1}: {item}")
            response = client.post("/api/v1/pantry", json=item, headers=auth_headers)
            print(f"🥫 Response: {response.status_code} - {response.text}")
            assert response.status_code == 200
            added_items.append(response.json())
        
        # Verify all items are in pantry
        print(f"🥫 Verifying pantry contents...")
        response = client.get("/api/v1/pantry", headers=auth_headers)
        print(f"🥫 Get pantry response: {response.status_code}")
        assert response.status_code == 200
        
        pantry_list = response.json()
        print(f"🥫 Pantry contains {len(pantry_list)} items")
        
        # Check each added item exists
        for original_item in pantry_items:
            found = False
            for pantry_item in pantry_list:
                if pantry_item["ingredient"]["id"] == original_item["ingredient_id"]:
                    assert pantry_item["quantity"] == original_item["quantity"]
                    assert pantry_item["expiration_date"] == original_item["expiration_date"]
                    found = True
                    break
            assert found, f"Item {original_item['ingredient_id']} not found in pantry"
        
        print(f"✅ All pantry items verified successfully")
    
    
    def test_pantry_item_updates(self, client, auth_headers, test_ingredient_ids):
        """Test updating pantry item quantities"""
        # Add initial item
        chicken_id = test_ingredient_ids['chicken_breast']
        item = {"ingredient_id": chicken_id, "quantity": 1.0, "expiration_date": "2024-12-30"}
        response = client.post("/api/v1/pantry", json=item, headers=auth_headers)
        assert response.status_code == 200
        
        # Update quantity
        update_data = {"ingredient_id": chicken_id, "quantity": 2.5, "expiration_date": "2024-12-30"}
        response = client.put(f"/api/v1/pantry/{chicken_id}", json=update_data, headers=auth_headers)
        print(f"🥫 Update response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/api/v1/pantry", headers=auth_headers)
        assert response.status_code == 200
        pantry_list = response.json()
        
        chicken_item = None
        for item in pantry_list:
            if item["ingredient"]["id"] == chicken_id:
                chicken_item = item
                break
        
        assert chicken_item is not None
        assert chicken_item["quantity"] == 2.5
    
    
    def test_pantry_expiration_dates(self, client, auth_headers, test_ingredient_ids):
        """Test pantry items with various expiration date formats"""
        items_with_dates = [
            {"ingredient_id": test_ingredient_ids['chicken_breast'], "quantity": 2.0, "expiration_date": "2024-12-25"},
            {"ingredient_id": test_ingredient_ids['rice'], "quantity": 1.0, "expiration_date": "2024-12-24"},
            {"ingredient_id": test_ingredient_ids['broccoli'], "quantity": 0.5, "expiration_date": "2025-01-05"}
        ]
        
        for item in items_with_dates:
            print(f"🥫 Adding item with expiration: {item}")
            response = client.post("/api/v1/pantry", json=item, headers=auth_headers)
            print(f"🥫 Response: {response.status_code}")
            assert response.status_code == 200
        
        # Get pantry and verify dates
        response = client.get("/api/v1/pantry", headers=auth_headers)
        assert response.status_code == 200
        pantry_list = response.json()
        
        for original_item in items_with_dates:
            found_item = None
            for pantry_item in pantry_list:
                if pantry_item["ingredient"]["id"] == original_item["ingredient_id"]:
                    found_item = pantry_item
                    break
            
            assert found_item is not None
            assert found_item["expiration_date"] == original_item["expiration_date"]
            print(f"✅ Date verified for {original_item['ingredient_id']}: {found_item['expiration_date']}")


class TestFamilyPantryIntegration:
    """Test interactions between family and pantry data"""
    
    def test_workflow_family_then_pantry(self, client, auth_headers, test_ingredient_ids):
        """Test the exact workflow: add family member, then add pantry items"""
        
        # Step 1: Add family member with dietary restrictions
        family_data = {
            "name": "Sarah Wilson",
            "age": 30,
            "dietary_restrictions": ["gluten-free"],
            "preferences": {
                "likes": ["chicken", "vegetables"],
                "dislikes": ["seafood"],
                "meal_preferences": "dinner"
            }
        }
        
        print(f"\n🔄 Step 1: Adding family member...")
        response = client.post("/api/v1/family/members", json=family_data, headers=auth_headers)
        print(f"🔄 Family response: {response.status_code}")
        assert response.status_code == 200
        family_id = response.json()["id"]
        
        # Step 2: Add pantry items that match dietary restrictions
        gluten_free_items = [
            {"ingredient_id": test_ingredient_ids['chicken_breast'], "quantity": 2.0, "expiration_date": "2024-12-31"},
            {"ingredient_id": test_ingredient_ids['rice'], "quantity": 3.0, "expiration_date": "2025-06-01"},
            {"ingredient_id": test_ingredient_ids['broccoli'], "quantity": 1.5, "expiration_date": "2024-12-26"}
        ]
        
        print(f"🔄 Step 2: Adding gluten-free pantry items...")
        for item in gluten_free_items:
            response = client.post("/api/v1/pantry", json=item, headers=auth_headers)
            print(f"🔄 Pantry item response: {response.status_code}")
            assert response.status_code == 200
        
        # Step 3: Verify both datasets exist
        print(f"🔄 Step 3: Verifying data existence...")
        
        # Check family
        response = client.get("/api/v1/family/members", headers=auth_headers)
        assert response.status_code == 200
        family_members = response.json()
        assert len(family_members) >= 1
        family = next(m for m in family_members if m["id"] == family_id)
        assert family["dietary_restrictions"] == ["gluten-free"]
        
        # Check pantry
        response = client.get("/api/v1/pantry", headers=auth_headers)
        assert response.status_code == 200
        pantry = response.json()
        assert len(pantry) >= 3
        
        print(f"✅ Integration test passed: family and pantry data consistent")
        
        return family_id, [item["ingredient_id"] for item in gluten_free_items]
    
    
    def test_data_ready_for_recommendations(self, client, auth_headers, test_ingredient_ids):
        """Test that data is in the correct format for recommendations endpoint"""
        
        # Add family and pantry data
        family_id, ingredient_ids = self.test_workflow_family_then_pantry(client, auth_headers, test_ingredient_ids)
        
        # Test recommendations status (should work)
        print(f"\n🤖 Testing recommendations readiness...")
        response = client.get("/api/v1/recommendations/status")
        print(f"🤖 Recommendations status: {response.status_code}")
        assert response.status_code == 200
        
        # Verify we have the minimum data needed for recommendations
        response = client.get("/api/v1/family/members", headers=auth_headers)
        family_data = response.json()
        assert len(family_data) > 0
        
        response = client.get("/api/v1/pantry", headers=auth_headers)
        pantry_data = response.json()
        assert len(pantry_data) > 0
        
        print(f"✅ Data ready for recommendations: {len(family_data)} family, {len(pantry_data)} pantry")
        
        # Return data for potential recommendations test
        return {
            "family_count": len(family_data),
            "pantry_count": len(pantry_data),
            "family_dietary_restrictions": family_data[0]["dietary_restrictions"],
            "pantry_ingredients": [item["ingredient"]["id"] for item in pantry_data]
        }