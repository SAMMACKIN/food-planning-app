#!/usr/bin/env python3
"""
Test the UUID fix with existing user
"""
import requests
import json
import jwt
import os
import sys

# Test the local API
API_BASE = "http://localhost:8001/api/v1"

def test_fix():
    """Test the UUID fix"""
    print("🔍 Testing UUID fix...")
    
    # Login with existing user
    login_data = {
        "email": "debug_userid_test@test.com",
        "password": "test123"
    }
    
    print("🔑 Logging in...")
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]
            print(f"✅ Got token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test retrieval
            print("🔍 Retrieving recipes...")
            response = requests.get(f"{API_BASE}/recipes", headers=headers)
            print(f"Retrieve response: {response.status_code}")
            print(f"Retrieve data: {response.text}")
            
            if response.status_code == 200:
                recipes = response.json()
                print(f"✅ Got {len(recipes)} recipes")
                if len(recipes) > 0:
                    print(f"✅ SUCCESS! Recipe retrieved: {recipes[0]['name']}")
                    return True
                else:
                    print("❌ Still no recipes returned")
                    return False
            else:
                print(f"❌ Retrieve failed: {response.text}")
                return False
        else:
            print(f"❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_fix()
    if success:
        print("\n🎉 UUID FIX SUCCESSFUL!")
    else:
        print("\n❌ UUID fix failed")