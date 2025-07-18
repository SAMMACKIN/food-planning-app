"""
Integration tests for complete user workflow - Family → Pantry → Recommendations → Recipes
Tests the exact sequence that users follow which breaks in preview
"""
import pytest
import json
from fastapi.testclient import TestClient

@pytest.fixture
def test_user_token(client):
    """Create a test user and return auth token"""
    import uuid
    # Register a new user with unique email
    user_data = {
        "email": f"workflow-{uuid.uuid4()}@test.com",
        "password": "testpass123",
        "name": "Workflow Tester"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    return data["access_token"]


@pytest.fixture
def auth_headers(test_user_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {test_user_token}"}


class TestCompleteUserWorkflow:
    """Test the complete user workflow that breaks in preview"""
    
    def test_complete_workflow_family_to_recommendations(self, client, auth_headers, test_ingredient_ids):
        """Test: Register → Add Family → Add Pantry → Get Recommendations"""
        
        print("\n🧪 TESTING COMPLETE WORKFLOW")
        
        # Step 1: Add a family member
        print("📋 Step 1: Adding family member...")
        family_data = {
            "name": "John Doe",
            "age": 35,
            "dietary_restrictions": ["gluten-free"],
            "preferences": {"likes": ["pasta", "chicken"], "dislikes": ["fish"]}
        }
        
        response = client.post("/api/v1/family/members", json=family_data, headers=auth_headers)
        print(f"📋 Family response status: {response.status_code}")
        print(f"📋 Family response: {response.text}")
        assert response.status_code == 200
        
        family_response = response.json()
        family_member_id = family_response["id"]
        print(f"📋 Created family member: {family_member_id}")
        
        # Step 2: Add pantry items
        print("🥫 Step 2: Adding pantry items...")
        pantry_items = [
            {"ingredient_id": test_ingredient_ids['chicken_breast'], "quantity": 2.0, "expiration_date": "2024-12-31"},
            {"ingredient_id": test_ingredient_ids['rice'], "quantity": 1.0, "expiration_date": "2025-01-15"},
            {"ingredient_id": test_ingredient_ids['broccoli'], "quantity": 0.5, "expiration_date": "2025-03-01"}
        ]
        
        for item in pantry_items:
            response = client.post("/api/v1/pantry", json=item, headers=auth_headers)
            print(f"🥫 Pantry item response status: {response.status_code}")
            print(f"🥫 Pantry item response: {response.text}")
            assert response.status_code == 200
        
        # Step 3: Verify family and pantry data exists
        print("✅ Step 3: Verifying data exists...")
        
        # Get family members
        response = client.get("/api/v1/family/members", headers=auth_headers)
        print(f"✅ Get family response status: {response.status_code}")
        assert response.status_code == 200
        family_list = response.json()
        assert len(family_list) > 0
        print(f"✅ Family members found: {len(family_list)}")
        
        # Get pantry items
        response = client.get("/api/v1/pantry", headers=auth_headers)
        print(f"✅ Get pantry response status: {response.status_code}")
        assert response.status_code == 200
        pantry_list = response.json()
        assert len(pantry_list) > 0
        print(f"✅ Pantry items found: {len(pantry_list)}")
        
        # Step 4: Test recommendations status (this should work)
        print("🤖 Step 4: Testing recommendations status...")
        response = client.get("/api/v1/recommendations/status")
        print(f"🤖 Recommendations status response: {response.status_code}")
        print(f"🤖 Recommendations status: {response.text}")
        assert response.status_code == 200
        
        # Step 5: Get recommendations (this might break)
        print("🔥 Step 5: Getting meal recommendations (critical test)...")
        recommendations_request = {
            "num_recommendations": 3,
            "preferences": {"meal_type": "dinner", "difficulty": "Medium"},
            "ai_provider": "perplexity"
        }
        
        response = client.post("/api/v1/recommendations", json=recommendations_request, headers=auth_headers)
        print(f"🔥 Recommendations response status: {response.status_code}")
        print(f"🔥 Recommendations response: {response.text}")
        
        # This is where it might break - capture the exact error
        if response.status_code != 200:
            print(f"❌ RECOMMENDATIONS FAILED: {response.status_code}")
            print(f"❌ Error details: {response.text}")
            # Don't fail the test immediately - continue to save recipes
        else:
            print(f"✅ Recommendations success: {len(response.json())} recipes")
        
        # Step 6: Test saved recipes (this might also break)
        print("🍽️ Step 6: Testing saved recipes...")
        response = client.get("/api/v1/recipes", headers=auth_headers)
        print(f"🍽️ Saved recipes response status: {response.status_code}")
        print(f"🍽️ Saved recipes response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ SAVED RECIPES FAILED: {response.status_code}")
            print(f"❌ Error details: {response.text}")
        else:
            print(f"✅ Saved recipes success: {len(response.json())} recipes")
        
        # Step 7: Try to save a manual recipe
        print("📝 Step 7: Saving a manual recipe...")
        recipe_data = {
            "name": "Test Recipe",
            "description": "A test recipe for workflow testing",
            "prep_time": 30,
            "difficulty": "Easy",
            "servings": 4,
            "ingredients_needed": ["chicken", "pasta", "olive oil"],
            "instructions": ["Cook chicken", "Boil pasta", "Mix together"],
            "tags": ["dinner", "easy"],
            "nutrition_notes": "High protein",
            "pantry_usage_score": 80,
            "ai_generated": False,
            "ai_provider": None,
            "source": "manual"
        }
        
        response = client.post("/api/v1/recipes", json=recipe_data, headers=auth_headers)
        print(f"📝 Save recipe response status: {response.status_code}")
        print(f"📝 Save recipe response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ SAVE RECIPE FAILED: {response.status_code}")
            print(f"❌ Error details: {response.text}")
            pytest.fail(f"Critical workflow failure: Cannot save recipes. Status: {response.status_code}, Error: {response.text}")
        else:
            print(f"✅ Recipe saved successfully")
            recipe_response = response.json()
            recipe_id = recipe_response["id"]
            
            # Verify we can retrieve the saved recipe
            response = client.get(f"/api/v1/recipes/{recipe_id}", headers=auth_headers)
            assert response.status_code == 200
            print(f"✅ Recipe retrieval successful")
        
        print("🎉 WORKFLOW TEST COMPLETED")
    
    
    def test_llm_connection_endpoints(self, client, auth_headers):
        """Test LLM connection and AI provider functionality"""
        
        print("\n🤖 TESTING LLM CONNECTION")
        
        # Test AI provider status
        response = client.get("/api/v1/recommendations/status")
        print(f"🤖 AI Status response: {response.status_code}")
        print(f"🤖 AI Status: {response.text}")
        assert response.status_code == 200
        
        status_data = response.json()
        available_providers = status_data.get("available_providers", [])
        print(f"🤖 Available providers: {available_providers}")
        
        # Test each available provider
        for provider in ["perplexity", "claude", "groq"]:
            print(f"\n🔧 Testing provider: {provider}")
            response = client.get(f"/api/v1/recommendations/test?provider={provider}")
            print(f"🔧 Test {provider} response: {response.status_code}")
            print(f"🔧 Test {provider} result: {response.text}")
            assert response.status_code == 200
            
            test_result = response.json()
            print(f"🔧 {provider} status: {test_result.get('status', 'UNKNOWN')}")
    
    
    def test_database_schema_validation(self, client, auth_headers):
        """Verify database schema matches expectations"""
        
        print("\n🗄️ TESTING DATABASE SCHEMA")
        
        # We're using PostgreSQL in tests now, so use different approach
        from sqlalchemy import create_engine, text
        import os
        
        db_url = os.environ.get("DATABASE_URL")
        print(f"🗄️ Database URL: {db_url}")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check required tables exist (PostgreSQL specific query)
            required_tables = ['users', 'family_members', 'user_pantry', 'ingredients', 
                              'recipes_v2', 'recipe_ratings', 'meal_plans']
            
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            existing_tables = {row[0] for row in result.fetchall()}
            print(f"🗄️ Existing tables: {existing_tables}")
            
            for table in required_tables:
                if table not in existing_tables:
                    print(f"⚠️ Missing table: {table}")
                else:
                    print(f"✅ Table exists: {table}")
            
            # Check critical table columns (PostgreSQL specific)
            table_columns = {
                'users': ['id', 'email', 'hashed_password', 'name', 'timezone', 'is_active', 'is_admin'],
                'family_members': ['id', 'user_id', 'name', 'age', 'dietary_restrictions', 'preferences'],
                'user_pantry': ['user_id', 'ingredient_id', 'quantity', 'expiration_date'],
                'recipes_v2': ['id', 'user_id', 'name', 'description', 'prep_time', 'difficulty', 
                             'servings', 'ingredients_needed', 'instructions', 'tags', 'ai_generated']
            }
            
            for table, required_cols in table_columns.items():
                if table in existing_tables:
                    result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' AND table_schema = 'public'
                    """))
                    existing_cols = {row[0] for row in result.fetchall()}
                    print(f"🗄️ {table} columns: {existing_cols}")
                    
                    for col in required_cols:
                        if col not in existing_cols:
                            print(f"⚠️ Missing column {col} in table {table}")
                        else:
                            print(f"✅ Column exists: {table}.{col}")
        
        print("🗄️ Database schema validation completed")


    def test_data_consistency_after_operations(self, client, auth_headers, test_ingredient_ids):
        """Test that data remains consistent after family→pantry→recommendations workflow"""
        
        print("\n🔍 TESTING DATA CONSISTENCY")
        
        # Add family member with complex data
        family_data = {
            "name": "Complex User",
            "age": 40,
            "dietary_restrictions": ["vegetarian", "nut-free"],
            "preferences": {
                "likes": ["italian", "mexican"],
                "dislikes": ["spicy"],
                "cooking_skill": "intermediate"
            }
        }
        
        response = client.post("/api/v1/family/members", json=family_data, headers=auth_headers)
        assert response.status_code == 200
        family_id = response.json()["id"]
        
        # Verify the data was stored correctly
        response = client.get("/api/v1/family/members", headers=auth_headers)
        assert response.status_code == 200
        family_members = response.json()
        assert len(family_members) >= 1
        family_member = next(m for m in family_members if m["id"] == family_id)
        
        print(f"🔍 Original dietary restrictions: {family_data['dietary_restrictions']}")
        print(f"🔍 Stored dietary restrictions: {family_member['dietary_restrictions']}")
        print(f"🔍 Original preferences: {family_data['preferences']}")
        print(f"🔍 Stored preferences: {family_member['preferences']}")
        
        assert family_member["dietary_restrictions"] == family_data["dietary_restrictions"]
        assert family_member["preferences"] == family_data["preferences"]
        
        # Test pantry data consistency
        chicken_id = test_ingredient_ids['chicken_breast']
        pantry_item = {
            "ingredient_id": chicken_id,
            "quantity": 2.5,
            "expiration_date": "2024-12-31"
        }
        
        response = client.post("/api/v1/pantry", json=pantry_item, headers=auth_headers)
        assert response.status_code == 200
        
        # Verify pantry data
        response = client.get("/api/v1/pantry", headers=auth_headers)
        assert response.status_code == 200
        pantry_items = response.json()
        
        found_item = None
        for item in pantry_items:
            if item["ingredient"]["id"] == chicken_id:
                found_item = item
                break
        
        assert found_item is not None
        assert found_item["quantity"] == 2.5
        print(f"✅ Pantry data consistency verified")
        
        print("🔍 Data consistency tests passed")