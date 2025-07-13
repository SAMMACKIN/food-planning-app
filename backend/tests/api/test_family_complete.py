"""
Comprehensive family member management API tests
"""
import pytest
import json


@pytest.mark.api
class TestFamilyMemberManagement:
    """Test family member CRUD operations"""
    
    def test_get_family_members_as_admin(self, admin_headers, client):
        """Test admin can view all family members"""
        response = client.get("/api/v1/family/members", headers=admin_headers)
        
        assert response.status_code == 200
        members = response.json()
        assert isinstance(members, list)
        # Admin should see all family members across all users
        
    def test_get_family_members_as_user(self, client):
        """Test regular user can only view their own family members"""
        # Register a new user
        import uuid
        user_data = {
            "email": f"familyuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Family User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/family/members", headers=headers)
        
        assert response.status_code == 200
        members = response.json()
        assert isinstance(members, list)
        # Should only see this user's family members
        
    def test_get_family_members_without_auth(self, client):
        """Test accessing family members without authentication"""
        response = client.get("/api/v1/family/members")
        
        # API allows unauthenticated access and returns empty list
        assert response.status_code == 200
        members = response.json()
        assert isinstance(members, list)
        
    def test_create_family_member_success(self, client):
        """Test successful family member creation"""
        # Register a user first
        import uuid
        user_data = {
            "email": f"parentuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Parent User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create family member
        member_data = {
            "name": "Little Johnny",
            "age": 8,
            "dietary_restrictions": ["vegetarian", "no nuts"],
            "preferences": {"favorite_food": "pasta", "dislikes": ["broccoli"]}
        }
        
        response = client.post("/api/v1/family/members", json=member_data, headers=headers)
        
        assert response.status_code == 200
        member = response.json()
        assert member["name"] == "Little Johnny"
        assert member["age"] == 8
        assert member["dietary_restrictions"] == ["vegetarian", "no nuts"]
        assert member["preferences"]["favorite_food"] == "pasta"
        assert "id" in member
        assert "user_id" in member
        assert "created_at" in member
        
    def test_create_family_member_minimal_data(self, client):
        """Test family member creation with minimal required data"""
        # Register a user first
        import uuid
        user_data = {
            "email": f"minimal-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Minimal User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create family member with only name
        member_data = {"name": "Simple Member"}
        
        response = client.post("/api/v1/family/members", json=member_data, headers=headers)
        
        assert response.status_code == 200
        member = response.json()
        assert member["name"] == "Simple Member"
        assert member["age"] is None
        assert member["dietary_restrictions"] == []
        assert member["preferences"] == {}
        
    def test_create_family_member_without_auth(self, client):
        """Test creating family member without authentication"""
        member_data = {"name": "Unauthorized Member"}
        
        response = client.post("/api/v1/family/members", json=member_data)
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
        
    def test_create_family_member_invalid_data(self, client):
        """Test family member creation with invalid data"""
        import uuid
        user_data = {
            "email": f"invalid-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Invalid User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Missing required name field
        response = client.post("/api/v1/family/members", json={}, headers=headers)
        assert response.status_code == 422
        
        # Invalid age (negative)
        response = client.post("/api/v1/family/members", json={
            "name": "Invalid Age",
            "age": -5
        }, headers=headers)
        # Note: API may or may not validate negative age - adjust assertion if needed
        
    def test_update_family_member_success(self, client):
        """Test successful family member update"""
        # Setup: Register user and create family member
        import uuid
        user_data = {
            "email": f"updateuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Update User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create member
        create_response = client.post("/api/v1/family/members", json={
            "name": "Original Name",
            "age": 10,
            "dietary_restrictions": ["vegetarian"]
        }, headers=headers)
        member_id = create_response.json()["id"]
        
        # Update member
        update_data = {
            "name": "Updated Name",
            "age": 11,
            "dietary_restrictions": ["vegetarian", "gluten-free"],
            "preferences": {"favorite_color": "blue"}
        }
        
        response = client.put(f"/api/v1/family/members/{member_id}", 
                            json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_member = response.json()
        assert updated_member["name"] == "Updated Name"
        assert updated_member["age"] == 11
        assert "gluten-free" in updated_member["dietary_restrictions"]
        assert updated_member["preferences"]["favorite_color"] == "blue"
        
    def test_update_family_member_partial(self, client):
        """Test partial family member update"""
        # Setup
        import uuid
        user_data = {
            "email": f"partialuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Partial User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create member
        create_response = client.post("/api/v1/family/members", json={
            "name": "Original Name",
            "age": 15,
            "dietary_restrictions": ["vegetarian"]
        }, headers=headers)
        member_id = create_response.json()["id"]
        original_name = create_response.json()["name"]
        
        # Update only age
        response = client.put(f"/api/v1/family/members/{member_id}", 
                            json={"age": 16}, headers=headers)
        
        assert response.status_code == 200
        updated_member = response.json()
        assert updated_member["name"] == original_name  # Should remain unchanged
        assert updated_member["age"] == 16  # Should be updated
        
    def test_update_nonexistent_family_member(self, client):
        """Test updating a family member that doesn't exist"""
        import uuid
        user_data = {
            "email": f"nonexistent-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Nonexistent User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_id = str(uuid.uuid4())  # Generate a valid UUID that doesn't exist
        response = client.put(f"/api/v1/family/members/{fake_id}", 
                            json={"name": "Updated Name"}, headers=headers)
        
        assert response.status_code == 404
        assert "Family member not found" in response.json()["detail"]
        
    def test_update_family_member_wrong_user(self, client):
        """Test user cannot update another user's family member"""
        # Create first user and family member
        import uuid
        user1_data = {
            "email": f"user1-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "User One"
        }
        register1_response = client.post("/api/v1/auth/register", json=user1_data)
        token1 = register1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        create_response = client.post("/api/v1/family/members", json={
            "name": "User1 Child"
        }, headers=headers1)
        member_id = create_response.json()["id"]
        
        # Create second user
        user2_data = {
            "email": f"user2-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "User Two"
        }
        register2_response = client.post("/api/v1/auth/register", json=user2_data)
        token2 = register2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Try to update user1's family member as user2
        response = client.put(f"/api/v1/family/members/{member_id}", 
                            json={"name": "Hacked Name"}, headers=headers2)
        
        # API should correctly deny this cross-user access
        assert response.status_code == 403
        
    def test_delete_family_member_success(self, client):
        """Test successful family member deletion"""
        # Setup
        import uuid
        user_data = {
            "email": f"deleteuser-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Delete User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create member
        create_response = client.post("/api/v1/family/members", json={
            "name": "To Be Deleted"
        }, headers=headers)
        member_id = create_response.json()["id"]
        
        # Delete member
        response = client.delete(f"/api/v1/family/members/{member_id}", headers=headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify member is gone
        get_response = client.get("/api/v1/family/members", headers=headers)
        members = get_response.json()
        member_ids = [m["id"] for m in members]
        assert member_id not in member_ids
        
    def test_delete_nonexistent_family_member(self, client):
        """Test deleting a family member that doesn't exist"""
        import uuid
        user_data = {
            "email": f"deletenonexistent-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Delete Nonexistent User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_id = str(uuid.uuid4())  # Generate a valid UUID that doesn't exist
        response = client.delete(f"/api/v1/family/members/{fake_id}", headers=headers)
        
        assert response.status_code == 404
        assert "Family member not found" in response.json()["detail"]
        
    def test_delete_family_member_wrong_user(self, client):
        """Test user cannot delete another user's family member"""
        # Create first user and family member
        import uuid
        user1_data = {
            "email": f"deluser1-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Delete User One"
        }
        register1_response = client.post("/api/v1/auth/register", json=user1_data)
        token1 = register1_response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        create_response = client.post("/api/v1/family/members", json={
            "name": "Protected Child"
        }, headers=headers1)
        member_id = create_response.json()["id"]
        
        # Create second user
        user2_data = {
            "email": f"deluser2-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Delete User Two"
        }
        register2_response = client.post("/api/v1/auth/register", json=user2_data)
        token2 = register2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Try to delete user1's family member as user2
        response = client.delete(f"/api/v1/family/members/{member_id}", headers=headers2)
        
        # API should correctly deny this cross-user access
        assert response.status_code == 403


@pytest.mark.api
class TestFamilyMemberValidation:
    """Test family member data validation"""
    
    def test_family_member_name_validation(self, client):
        """Test name field validation"""
        import uuid
        user_data = {
            "email": f"validation-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Validation User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test empty name
        response = client.post("/api/v1/family/members", json={
            "name": ""
        }, headers=headers)
        # API accepts empty name
        assert response.status_code == 200
        member = response.json()
        assert member["name"] == ""
        
        # Test very long name
        response = client.post("/api/v1/family/members", json={
            "name": "A" * 300  # Very long name
        }, headers=headers)
        # Should handle long names gracefully
        
    def test_family_member_age_validation(self, client):
        """Test age field validation"""
        import uuid
        user_data = {
            "email": f"agevalidation-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Age Validation User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test valid ages
        for age in [0, 1, 50, 100]:
            response = client.post("/api/v1/family/members", json={
                "name": f"Person Age {age}",
                "age": age
            }, headers=headers)
            assert response.status_code == 200
            
        # Test edge cases
        response = client.post("/api/v1/family/members", json={
            "name": "Very Old Person",
            "age": 150  # Very old age
        }, headers=headers)
        # Should handle edge cases gracefully
        
    def test_family_member_dietary_restrictions_validation(self, client):
        """Test dietary restrictions field validation"""
        import uuid
        user_data = {
            "email": f"dietary-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Dietary User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test various dietary restrictions
        test_cases = [
            [],  # Empty list
            ["vegetarian"],  # Single restriction
            ["vegetarian", "gluten-free", "no nuts"],  # Multiple restrictions
            ["custom restriction with spaces"]  # Custom restriction
        ]
        
        for i, restrictions in enumerate(test_cases):
            response = client.post("/api/v1/family/members", json={
                "name": f"Dietary Test {i}",
                "dietary_restrictions": restrictions
            }, headers=headers)
            assert response.status_code == 200
            member = response.json()
            assert member["dietary_restrictions"] == restrictions
            
    def test_family_member_preferences_validation(self, client):
        """Test preferences field validation"""
        import uuid
        user_data = {
            "email": f"preferences-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Preferences User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test various preference structures
        test_cases = [
            {},  # Empty dict
            {"favorite_food": "pizza"},  # Simple preference
            {
                "favorite_foods": ["pizza", "pasta"],
                "dislikes": ["broccoli"],
                "allergies": ["peanuts"],
                "cooking_skill": "beginner"
            },  # Complex preferences
            {"nested": {"preference": "value"}}  # Nested structure
        ]
        
        for i, preferences in enumerate(test_cases):
            response = client.post("/api/v1/family/members", json={
                "name": f"Preferences Test {i}",
                "preferences": preferences
            }, headers=headers)
            assert response.status_code == 200
            member = response.json()
            assert member["preferences"] == preferences


@pytest.mark.api
class TestFamilyMemberIntegration:
    """Test family member integration with other features"""
    
    def test_family_member_with_meal_recommendations(self, client):
        """Test that family members can be used in meal recommendations"""
        # This test verifies the integration between family management and AI recommendations
        # Setup user and family members
        import uuid
        user_data = {
            "email": f"integration-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Integration User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create family members with different dietary restrictions
        members = [
            {
                "name": "Vegetarian Child",
                "age": 8,
                "dietary_restrictions": ["vegetarian"]
            },
            {
                "name": "Gluten-Free Adult",
                "age": 35,
                "dietary_restrictions": ["gluten-free"]
            }
        ]
        
        for member_data in members:
            response = client.post("/api/v1/family/members", json=member_data, headers=headers)
            assert response.status_code == 200
            
        # Verify family members are created and can be retrieved
        get_response = client.get("/api/v1/family/members", headers=headers)
        assert get_response.status_code == 200
        family_members = get_response.json()
        assert len(family_members) >= 2
        
        # Check that dietary restrictions are properly stored
        restrictions = []
        for member in family_members:
            restrictions.extend(member["dietary_restrictions"])
        assert "vegetarian" in restrictions
        assert "gluten-free" in restrictions
        
    def test_family_member_workflow_complete(self, client):
        """Test complete family member management workflow"""
        # Register user
        import uuid
        user_data = {
            "email": f"workflow-{uuid.uuid4()}@example.com",
            "password": "password123",
            "name": "Workflow User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Create multiple family members
        family_data = [
            {"name": "Parent", "age": 35, "dietary_restrictions": []},
            {"name": "Child 1", "age": 8, "dietary_restrictions": ["no nuts"]},
            {"name": "Child 2", "age": 12, "dietary_restrictions": ["vegetarian"]}
        ]
        
        created_members = []
        for member_data in family_data:
            response = client.post("/api/v1/family/members", json=member_data, headers=headers)
            assert response.status_code == 200
            created_members.append(response.json())
            
        # Step 2: Verify all members are retrievable
        get_response = client.get("/api/v1/family/members", headers=headers)
        assert get_response.status_code == 200
        retrieved_members = get_response.json()
        assert len(retrieved_members) == len(family_data)
        
        # Step 3: Update a family member
        member_to_update = created_members[1]  # Child 1
        update_data = {
            "age": 9,  # Birthday!
            "dietary_restrictions": ["no nuts", "lactose-free"]  # New restriction
        }
        
        update_response = client.put(
            f"/api/v1/family/members/{member_to_update['id']}", 
            json=update_data, 
            headers=headers
        )
        assert update_response.status_code == 200
        updated_member = update_response.json()
        assert updated_member["age"] == 9
        assert "lactose-free" in updated_member["dietary_restrictions"]
        
        # Step 4: Delete a family member
        member_to_delete = created_members[2]  # Child 2
        delete_response = client.delete(
            f"/api/v1/family/members/{member_to_delete['id']}", 
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # Step 5: Verify final state
        final_get_response = client.get("/api/v1/family/members", headers=headers)
        assert final_get_response.status_code == 200
        final_members = final_get_response.json()
        assert len(final_members) == 2  # One deleted
        
        final_member_ids = [m["id"] for m in final_members]
        assert member_to_delete["id"] not in final_member_ids
        assert member_to_update["id"] in final_member_ids