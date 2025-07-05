#!/usr/bin/env python3
"""
Test script to debug user_id matching issue
"""
import requests
import json
import jwt
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, '/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend')

# Test the local API
API_BASE = "http://localhost:8001/api/v1"

def decode_token(token):
    """Decode JWT token to see user_id"""
    try:
        # Note: This will fail signature verification, but we can still see the payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Could not decode token: {e}")
        return None

def test_user_id_matching():
    """Test to see exactly what user_id values are being used"""
    print("🔍 Testing user_id matching...")
    
    # Register a test user
    user_data = {
        "email": "debug_userid_test@test.com",
        "password": "test123",
        "name": "Debug User ID Test"
    }
    
    print("📝 Registering test user...")
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"Register response: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]
            print(f"✅ Got token: {token[:20]}...")
            
            # Decode token to see user_id
            decoded = decode_token(token)
            if decoded:
                print(f"🔍 Token payload: {decoded}")
                print(f"🔍 Token user_id: {decoded.get('sub', 'NOT_FOUND')}")
                print(f"🔍 Token user_id type: {type(decoded.get('sub', 'NOT_FOUND'))}")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Save a test recipe
            recipe_data = {
                "name": "User ID Test Recipe",
                "description": "Testing user ID matching",
                "prep_time": 10,
                "difficulty": "Easy",
                "servings": 1,
                "ingredients_needed": ["test ingredient"],
                "instructions": ["Test step"],
                "tags": ["test"],
                "nutrition_notes": "Test",
                "pantry_usage_score": 25,
                "ai_generated": False,
                "ai_provider": None,
                "source": "manual"
            }
            
            print("💾 Saving test recipe...")
            response = requests.post(f"{API_BASE}/recipes", json=recipe_data, headers=headers)
            print(f"Save response: {response.status_code}")
            
            if response.status_code == 200:
                saved_recipe = response.json()
                print(f"✅ Recipe saved!")
                print(f"🔍 Saved recipe user_id: {saved_recipe['user_id']}")
                print(f"🔍 Saved recipe user_id type: {type(saved_recipe['user_id'])}")
                
                # Compare user_ids
                token_user_id = decoded.get('sub') if decoded else None
                saved_user_id = saved_recipe['user_id']
                
                print(f"🔍 Token user_id == Saved user_id: {token_user_id == saved_user_id}")
                print(f"🔍 Token user_id str == Saved user_id str: {str(token_user_id) == str(saved_user_id)}")
                
                # Now test retrieval
                print("🔍 Retrieving recipes...")
                response = requests.get(f"{API_BASE}/recipes", headers=headers)
                print(f"Retrieve response: {response.status_code}")
                
                if response.status_code == 200:
                    recipes = response.json()
                    print(f"✅ Got {len(recipes)} recipes")
                    if len(recipes) == 0:
                        print("❌ ISSUE CONFIRMED: Recipe was saved but not retrieved!")
                    else:
                        print(f"✅ Recipe retrieved successfully: {recipes[0]['name']}")
                else:
                    print(f"❌ Retrieve failed: {response.text}")
            else:
                print(f"❌ Save failed: {response.text}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_user_id_matching()