#!/usr/bin/env python3
"""
Create admin account for local development
"""
import requests
import json

def create_local_admin():
    base_url = "http://localhost:8001/api/v1"
    
    print("🔧 Creating local admin account...")
    
    # Admin user data
    admin_user = {
        "email": "admin",
        "password": "admin123", 
        "name": "Admin User"
    }
    
    print(f"Creating admin user: {admin_user['email']}")
    
    try:
        # Register admin user
        response = requests.post(f"{base_url}/auth/register", json=admin_user)
        print(f"Registration status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Admin user created successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Admin user already exists")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
            
        # Test login
        print("\nTesting admin login...")
        login_data = {
            "email": admin_user["email"],
            "password": admin_user["password"]
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Admin login successful")
            print(f"Token: {access_token[:30]}..." if access_token else "No token")
            
            # Test auth endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ Authenticated as: {user_info.get('email')} ({user_info.get('name')})")
                print(f"User ID: {user_info.get('id')}")
            else:
                print(f"❌ Auth check failed: {response.text}")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_local_admin()