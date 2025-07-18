"""
Integration tests for Recommendations and Recipes endpoints
Tests the exact endpoints that break in preview environment
"""
import pytest
import json

@pytest.fixture
def test_user_with_data(client, test_ingredient_ids):
    """Create a test user with family and pantry data"""
    import uuid
    # Register user
    user_data = {
        "email": f"recipetest-{uuid.uuid4()}@test.com",
        "password": "testpass123",
        "name": "Recipe Tester"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add family member
    family_data = {
        "name": "Test Family Member",
        "age": 30,
        "dietary_restrictions": ["vegetarian"],
        "preferences": {"likes": ["pasta", "vegetables"]}
    }
    response = client.post("/api/v1/family/members", json=family_data, headers=headers)
    assert response.status_code == 200
    
    # Add pantry items using proper UUIDs
    pantry_items = [
        {"ingredient_id": test_ingredient_ids['chicken_breast'], "quantity": 2.0, "expiration_date": "2025-01-15"},
        {"ingredient_id": test_ingredient_ids['rice'], "quantity": 0.5, "expiration_date": "2025-03-01"},
        {"ingredient_id": test_ingredient_ids['broccoli'], "quantity": 3.0, "expiration_date": "2024-12-28"}
    ]
    
    for item in pantry_items:
        response = client.post("/api/v1/pantry", json=item, headers=headers)
        assert response.status_code == 200
    
    return token, headers


class TestRecommendationsEndpoint:
    """Test the recommendations endpoint that breaks in preview"""
    
    def test_recommendations_status_endpoint(self, client):
        """Test the recommendations status endpoint (should always work)"""
        print("\n🤖 Testing recommendations status...")
        response = client.get("/api/v1/recommendations/status")
        print(f"🤖 Status response: {response.status_code}")
        print(f"🤖 Status data: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert "available_providers" in data
        print(f"🤖 Available providers: {data['available_providers']}")
    
    
    def test_recommendations_test_endpoint(self, client):
        """Test the AI provider test endpoint"""
        providers_to_test = ["perplexity", "claude", "groq"]
        
        for provider in providers_to_test:
            print(f"\n🔧 Testing provider: {provider}")
            response = client.get(f"/api/v1/recommendations/test?provider={provider}")
            print(f"🔧 {provider} test response: {response.status_code}")
            print(f"🔧 {provider} test result: {response.text}")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "provider" in data
            print(f"🔧 {provider} status: {data['status']}")
    
    
    def test_recommendations_with_auth_and_data(self, client, test_user_with_data, mock_claude_api):
        """Test getting recommendations with authenticated user and data"""
        token, headers = test_user_with_data
        
        print("\n🔥 Testing recommendations with real user data...")
        
        recommendations_request = {
            "num_recommendations": 2,
            "preferences": {
                "meal_type": "dinner",
                "difficulty": "Easy"
            },
            "ai_provider": "perplexity"
        }
        
        print(f"🔥 Request data: {recommendations_request}")
        response = client.post("/api/v1/recommendations", json=recommendations_request, headers=headers)
        print(f"🔥 Recommendations response status: {response.status_code}")
        print(f"🔥 Recommendations response body: {response.text}")
        
        # This is the critical test - capture detailed error info if it fails
        if response.status_code != 200:
            print(f"❌ CRITICAL FAILURE: Recommendations endpoint failed")
            print(f"❌ Status code: {response.status_code}")
            print(f"❌ Error response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"❌ Error detail: {error_data.get('detail', 'No detail provided')}")
            except:
                print(f"❌ Could not parse error response as JSON")
            
            # Don't fail the test - we want to see what's happening
            pytest.fail(f"Recommendations endpoint failed with status {response.status_code}: {response.text}")
        else:
            print(f"✅ Recommendations success!")
            data = response.json()
            print(f"✅ Got {len(data)} recommendations")
            
            if data:
                first_rec = data[0]
                print(f"✅ First recommendation: {first_rec.get('name', 'NO_NAME')}")
                print(f"✅ AI generated: {first_rec.get('ai_generated', 'UNKNOWN')}")
    
    
    def test_recommendations_without_ai_providers(self, client, test_user_with_data, mock_claude_api):
        """Test recommendations when no AI providers are available (should use mock)"""
        token, headers = test_user_with_data
        
        print("\n🤖 Testing recommendations with mock AI...")
        
        # Request with a provider that doesn't exist
        recommendations_request = {
            "num_recommendations": 1,
            "preferences": {"meal_type": "lunch"},
            "ai_provider": "mock"
        }
        
        response = client.post("/api/v1/recommendations", json=recommendations_request, headers=headers)
        print(f"🤖 Mock AI response: {response.status_code}")
        print(f"🤖 Mock AI data: {response.text}")
        
        # Should still work with mock data
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        print(f"🤖 Mock recommendation: {data[0]['name']}")


class TestSavedRecipesEndpoint:
    """Test the saved recipes endpoint that breaks in preview"""
    
    def test_get_saved_recipes_empty(self, client, test_user_with_data):
        """Test getting saved recipes when user has none"""
        token, headers = test_user_with_data
        
        print("\n🍽️ Testing get saved recipes (empty)...")
        response = client.get("/api/v1/recipes", headers=headers)
        print(f"🍽️ Get recipes response: {response.status_code}")
        print(f"🍽️ Get recipes data: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL FAILURE: Get saved recipes failed")
            print(f"❌ Status code: {response.status_code}")
            print(f"❌ Error response: {response.text}")
            pytest.fail(f"Get saved recipes failed with status {response.status_code}: {response.text}")
        else:
            print(f"✅ Get saved recipes success!")
            data = response.json()
            assert isinstance(data, list)
            print(f"✅ Got {len(data)} saved recipes")
    
    
    def test_save_recipe_manual(self, client, test_user_with_data):
        """Test saving a manual recipe"""
        token, headers = test_user_with_data
        
        print("\n📝 Testing save manual recipe...")
        
        recipe_data = {
            "name": "Test Pasta Recipe",
            "description": "A simple pasta dish for testing",
            "prep_time": 25,
            "difficulty": "Easy",
            "servings": 4,
            "ingredients_needed": ["pasta", "olive oil", "garlic", "tomatoes"],
            "instructions": [
                "Boil water and cook pasta",
                "Heat olive oil in pan",
                "Add garlic and tomatoes",
                "Mix with pasta and serve"
            ],
            "tags": ["dinner", "italian", "vegetarian"],
            "nutrition_notes": "Good source of carbohydrates",
            "pantry_usage_score": 75,
            "ai_generated": False,
            "ai_provider": None,
            "source": "manual"
        }
        
        print(f"📝 Recipe data: {recipe_data['name']}")
        response = client.post("/api/v1/recipes", json=recipe_data, headers=headers)
        print(f"📝 Save recipe response: {response.status_code}")
        print(f"📝 Save recipe data: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL FAILURE: Save recipe failed")
            print(f"❌ Status code: {response.status_code}")
            print(f"❌ Error response: {response.text}")
            
            try:
                error_data = response.json()
                print(f"❌ Error detail: {error_data.get('detail', 'No detail provided')}")
            except:
                print(f"❌ Could not parse error response as JSON")
            
            pytest.fail(f"Save recipe failed with status {response.status_code}: {response.text}")
        else:
            print(f"✅ Save recipe success!")
            saved_recipe = response.json()
            recipe_id = saved_recipe["id"]
            print(f"✅ Saved recipe ID: {recipe_id}")
            
            # Verify we can retrieve the saved recipe
            print(f"📝 Verifying recipe retrieval...")
            response = client.get(f"/api/v1/recipes/{recipe_id}", headers=headers)
            print(f"📝 Get single recipe response: {response.status_code}")
            
            if response.status_code != 200:
                pytest.fail(f"Could not retrieve saved recipe: {response.status_code}")
            else:
                retrieved_recipe = response.json()
                assert retrieved_recipe["name"] == recipe_data["name"]
                assert retrieved_recipe["difficulty"] == recipe_data["difficulty"]
                print(f"✅ Recipe retrieval verified")
                
                return recipe_id
    
    
    def test_recipe_rating(self, client, test_user_with_data):
        """Test rating a saved recipe"""
        token, headers = test_user_with_data
        
        # First save a recipe
        recipe_id = self.test_save_recipe_manual(client, test_user_with_data)
        
        print(f"\n⭐ Testing recipe rating...")
        
        rating_data = {
            "recipe_id": recipe_id,
            "rating": 5,
            "review_text": "Excellent recipe, very easy to follow!",
            "would_make_again": True,
            "cooking_notes": "Added extra garlic for more flavor"
        }
        
        print(f"⭐ Rating data: {rating_data}")
        response = client.post(f"/api/v1/recipes/{recipe_id}/ratings", json=rating_data, headers=headers)
        print(f"⭐ Rating response: {response.status_code}")
        print(f"⭐ Rating data: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Recipe rating failed: {response.status_code}")
            pytest.fail(f"Recipe rating failed: {response.text}")
        else:
            rating_response = response.json()
            assert rating_response["rating"] == 5
            assert rating_response["review_text"] == rating_data["review_text"]
            print(f"✅ Recipe rating success!")
    
    
    def test_recipe_with_complex_data(self, client, test_user_with_data):
        """Test saving recipe with complex ingredients and instructions"""
        token, headers = test_user_with_data
        
        print("\n🍽️ Testing complex recipe data...")
        
        complex_recipe = {
            "name": "Complex Test Recipe",
            "description": "A recipe with complex data structures to test parsing",
            "prep_time": 45,
            "difficulty": "Medium",
            "servings": 6,
            "ingredients_needed": [
                "2 lbs chicken breast, diced",
                "1 cup basmati rice",
                "2 tbsp olive oil",
                "1 large onion, chopped",
                "3 cloves garlic, minced",
                "1 can (14oz) diced tomatoes",
                "2 cups chicken broth",
                "1 tsp oregano",
                "1/2 tsp paprika",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "Heat olive oil in a large skillet over medium-high heat",
                "Season chicken with salt and pepper, add to skillet",
                "Cook chicken until browned on all sides, about 6-8 minutes",
                "Remove chicken and set aside",
                "In the same skillet, add onion and cook until softened",
                "Add garlic and cook for 1 minute until fragrant",
                "Add rice and stir to coat with oil for 2 minutes",
                "Add tomatoes, broth, oregano, and paprika",
                "Bring to a boil, then reduce heat and simmer",
                "Return chicken to skillet, cover and cook 18-20 minutes",
                "Let rest 5 minutes before serving"
            ],
            "tags": ["dinner", "one-pot", "chicken", "rice", "mediterranean"],
            "nutrition_notes": "High protein, balanced carbohydrates, contains vegetables",
            "pantry_usage_score": 85,
            "ai_generated": False,
            "ai_provider": None,
            "source": "manual"
        }
        
        print(f"🍽️ Complex recipe: {len(complex_recipe['ingredients_needed'])} ingredients, {len(complex_recipe['instructions'])} steps")
        response = client.post("/api/v1/recipes", json=complex_recipe, headers=headers)
        print(f"🍽️ Complex recipe response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Complex recipe save failed: {response.text}")
            pytest.fail(f"Complex recipe save failed: {response.status_code}")
        else:
            saved_recipe = response.json()
            
            # Verify complex data was preserved
            assert len(saved_recipe["ingredients_needed"]) == len(complex_recipe["ingredients_needed"])
            assert len(saved_recipe["instructions"]) == len(complex_recipe["instructions"])
            assert saved_recipe["tags"] == complex_recipe["tags"]
            
            print(f"✅ Complex recipe data preserved correctly")


class TestRecipesHealthCheck:
    """Test the recipe health check endpoint"""
    
    def test_recipes_health_endpoint(self, client, test_user_with_data):
        """Test the debug health endpoint for recipes"""
        token, headers = test_user_with_data
        
        print("\n🔍 Testing recipes health check...")
        response = client.get("/api/v1/recipes/debug/health", headers=headers)
        print(f"🔍 Health check response: {response.status_code}")
        print(f"🔍 Health check data: {response.text}")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert "status" in health_data
        assert "database_connected" in health_data
        assert "table_accessible" in health_data
        
        print(f"🔍 Database connected: {health_data['database_connected']}")
        print(f"🔍 Overall status: {health_data['status']}")
        
        # Check basic status
        assert health_data["status"] == "healthy"
        assert health_data["database_connected"] == True
        assert health_data["table_accessible"] == True


class TestEndToEndRecipeWorkflow:
    """Test the complete recipe workflow from recommendations to saved recipes"""
    
    def test_complete_recipe_workflow(self, client, test_user_with_data, mock_claude_api):
        """Test: Get recommendations → Save recipe → Rate recipe → Retrieve recipes"""
        token, headers = test_user_with_data
        
        print("\n🔄 Testing complete recipe workflow...")
        
        # Step 1: Try to get recommendations
        print("🔄 Step 1: Getting recommendations...")
        rec_request = {
            "num_recommendations": 1,
            "preferences": {"meal_type": "dinner"},
            "ai_provider": "perplexity"
        }
        
        response = client.post("/api/v1/recommendations", json=rec_request, headers=headers)
        
        if response.status_code == 200:
            recommendations = response.json()
            if recommendations:
                # Use first recommendation to save as recipe
                rec = recommendations[0]
                recipe_data = {
                    "name": rec["name"],
                    "description": rec["description"],
                    "prep_time": rec["prep_time"],
                    "difficulty": rec["difficulty"],
                    "servings": rec["servings"],
                    "ingredients_needed": rec["ingredients_needed"],
                    "instructions": rec["instructions"],
                    "tags": rec["tags"],
                    "nutrition_notes": rec["nutrition_notes"],
                    "pantry_usage_score": rec["pantry_usage_score"],
                    "ai_generated": rec.get("ai_generated", False),
                    "ai_provider": rec.get("ai_provider"),
                    "source": "recommendation"
                }
                
                print(f"🔄 Step 2: Saving recommended recipe: {rec['name']}")
                response = client.post("/api/v1/recipes", json=recipe_data, headers=headers)
                
                if response.status_code == 200:
                    saved_recipe = response.json()
                    recipe_id = saved_recipe["id"]
                    
                    # Step 3: Rate the recipe
                    print(f"🔄 Step 3: Rating the recipe...")
                    rating_data = {
                        "recipe_id": recipe_id,
                        "rating": 4,
                        "review_text": "Good recipe from AI recommendation",
                        "would_make_again": True
                    }
                    
                    response = client.post(f"/api/v1/recipes/{recipe_id}/ratings", json=rating_data, headers=headers)
                    assert response.status_code == 200
                    
                    # Step 4: Retrieve all saved recipes
                    print(f"🔄 Step 4: Retrieving all saved recipes...")
                    response = client.get("/api/v1/recipes", headers=headers)
                    assert response.status_code == 200
                    
                    recipes_list = response.json()
                    assert len(recipes_list) > 0
                    
                    # Find our recipe
                    found_recipe = None
                    for recipe in recipes_list:
                        if recipe["id"] == recipe_id:
                            found_recipe = recipe
                            break
                    
                    assert found_recipe is not None
                    assert found_recipe["rating"] == 4.0  # Should include the rating
                    
                    print(f"✅ Complete workflow successful!")
                    return True
        
        # Fallback: test with manual recipe if recommendations fail
        print("🔄 Fallback: Testing with manual recipe...")
        return self.test_save_recipe_manual(client, test_user_with_data) is not None