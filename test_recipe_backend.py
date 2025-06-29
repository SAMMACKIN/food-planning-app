#!/usr/bin/env python3
"""
Test recipe saving functionality directly against the backend
"""
import requests
import json

def test_recipe_backend():
    base_url = "http://localhost:8001/api/v1"
    
    print("🧪 Testing Recipe Backend Functionality")
    print("=" * 50)
    
    # Test 1: Check if recipes endpoint exists
    print("1. Testing recipes endpoint availability...")
    try:
        response = requests.get(f"{base_url}/recipes")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (requires authentication)")
        elif response.status_code == 404:
            print("   ❌ Endpoint not found")
            return
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Try to register a test user
    print("\n2. Creating test user...")
    import time
    timestamp = int(time.time())
    test_user = {
        "email": f"test{timestamp}@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=test_user)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ User created successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("   ✅ User already exists")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Login and get token
    print("\n3. Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("   ✅ Login successful")
            print(f"   Token: {access_token[:20]}..." if access_token else "No token")
            
            if not access_token:
                print("   ❌ No access token received")
                return
                
            # Test 4: Try to save a recipe
            print("\n4. Testing recipe saving...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            test_recipe = {
                "name": "Test Recipe",
                "description": "A test recipe",
                "prep_time": 30,
                "difficulty": "Easy",
                "servings": 4,
                "ingredients_needed": [
                    {"name": "test ingredient", "quantity": "1", "unit": "cup"}
                ],
                "instructions": ["Step 1: Test"],
                "tags": ["test"],
                "nutrition_notes": "Test nutrition",
                "pantry_usage_score": 80,
                "ai_generated": False,
                "source": "test"
            }
            
            response = requests.post(f"{base_url}/recipes", json=test_recipe, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:300]}...")
            
            if response.status_code in [200, 201]:
                print("   ✅ Recipe saved successfully!")
                saved_recipe = response.json()
                recipe_id = saved_recipe.get("id")
                
                # Test 5: Fetch the saved recipe
                print("\n5. Testing recipe retrieval...")
                response = requests.get(f"{base_url}/recipes", headers=headers)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    recipes = response.json()
                    print(f"   ✅ Found {len(recipes)} recipes")
                    test_recipe_found = any(r.get("id") == recipe_id for r in recipes)
                    print(f"   Test recipe found: {'✅' if test_recipe_found else '❌'}")
                else:
                    print(f"   ❌ Failed to fetch recipes: {response.text[:200]}")
            else:
                print("   ❌ Recipe saving failed")
                
        else:
            print(f"   ❌ Login failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_recipe_backend()