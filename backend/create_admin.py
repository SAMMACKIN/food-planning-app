#!/usr/bin/env python3
"""
Script to create admin user in PostgreSQL database
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.auth_service import AuthService
from app.core.database_service import init_db

def main():
    print("🔧 Initializing database...")
    init_db()
    
    print("🔑 Creating admin user...")
    admin_user = AuthService.create_user(
        email="admin",
        name="Admin User", 
        password="admin123",
        is_admin=True
    )
    
    if admin_user:
        print("✅ Admin user created successfully!")
        print(f"   Email: admin")
        print(f"   Password: admin123")
        print(f"   Name: {admin_user['name']}")
        print(f"   Admin: {admin_user['is_admin']}")
    else:
        print("❌ Failed to create admin user (may already exist)")
        
        # Check if user exists
        existing = AuthService.get_user_by_email("admin")
        if existing:
            print("✅ Admin user already exists!")
            print(f"   Email: admin")
            print(f"   Name: {existing['name']}")
            print(f"   Admin: {existing['is_admin']}")

if __name__ == "__main__":
    main()