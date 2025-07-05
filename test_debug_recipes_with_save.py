#!/usr/bin/env python3
"""
Test script to debug the recipes endpoint with saving a recipe first
"""
import requests
import json
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, '/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend')

# Test the local API
API_BASE = "http://localhost:8001/api/v1"

def test_save_and_retrieve_recipe():
    """Test saving a recipe and then retrieving it"""
    print("🔍 Testing save and retrieve recipe workflow...")
    
    # First, register a test user
    user_data = {
        "email": "debug_save_test@test.com",
        "password": "test123",
        "name": "Debug Save Test User"
    }
    
    print("📝 Registering test user...")
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"Register response: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]
            print(f"✅ Got token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Save a test recipe
            recipe_data = {
                "name": "Debug Test Recipe",
                "description": "A test recipe for debugging",
                "prep_time": 15,
                "difficulty": "Easy",
                "servings": 2,
                "ingredients_needed": ["test ingredient 1", "test ingredient 2"],
                "instructions": ["Step 1", "Step 2"],
                "tags": ["test", "debug"],
                "nutrition_notes": "Test nutrition",
                "pantry_usage_score": 50,
                "ai_generated": False,
                "ai_provider": None,
                "source": "manual"
            }
            
            print("💾 Saving test recipe...")
            response = requests.post(f"{API_BASE}/recipes", json=recipe_data, headers=headers)
            print(f"Save response: {response.status_code}")
            print(f"Save data: {response.text}")
            
            if response.status_code == 200:
                saved_recipe = response.json()
                print(f"✅ Recipe saved with ID: {saved_recipe['id']}")
                
                # Now try to retrieve recipes
                print("🔍 Retrieving recipes...")
                response = requests.get(f"{API_BASE}/recipes", headers=headers)
                print(f"Retrieve response: {response.status_code}")
                print(f"Retrieve data: {response.text}")
                
                if response.status_code == 200:
                    recipes = response.json()
                    print(f"✅ Got {len(recipes)} recipes")
                    if len(recipes) > 0:
                        print(f"First recipe: {recipes[0]['name']}")
                    else:
                        print("❌ No recipes returned despite saving one!")
                else:
                    print(f"❌ Retrieve failed: {response.text}")
            else:
                print(f"❌ Save failed: {response.text}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_save_and_retrieve_recipe()