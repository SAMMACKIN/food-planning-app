#!/usr/bin/env python3
"""
Test script to debug the recipes endpoint locally
"""
import requests
import json
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, '/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend')

# Test the local API
API_BASE = "http://localhost:8001/api/v1"

def test_auth_and_recipes():
    """Test authentication and recipes endpoint"""
    print("🔍 Testing authentication and recipes endpoint...")
    
    # First, register a test user
    user_data = {
        "email": "debug_test@test.com",
        "password": "test123",
        "name": "Debug Test User"
    }
    
    print("📝 Registering test user...")
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"Register response: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]
            print(f"✅ Got token: {token[:20]}...")
            
            # Test recipes endpoint
            headers = {"Authorization": f"Bearer {token}"}
            print("🍽️ Testing recipes endpoint...")
            
            response = requests.get(f"{API_BASE}/recipes", headers=headers)
            print(f"Recipes response: {response.status_code}")
            print(f"Recipes data: {response.text}")
            
            if response.status_code == 200:
                recipes = response.json()
                print(f"✅ Got {len(recipes)} recipes")
            else:
                print(f"❌ Recipes failed: {response.text}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_auth_and_recipes()