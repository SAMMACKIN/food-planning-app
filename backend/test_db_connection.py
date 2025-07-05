#!/usr/bin/env python3
"""Test PostgreSQL connection and create admin user"""
import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing PostgreSQL connection...")
    
    # Test psycopg2 connection
    import psycopg2
    conn = psycopg2.connect("postgresql://postgres:whbutb2012@localhost:5432/food_planning_dev")
    cur = conn.cursor()
    
    print("✅ PostgreSQL connection successful")
    
    # Check if users table exists
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users';")
    if cur.fetchone():
        print("✅ Users table exists")
    else:
        print("❌ Users table does not exist")
    
    # Try to import app modules
    from app.core.database_service import init_db
    from app.core.auth_service import AuthService
    
    print("✅ App modules imported successfully")
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Check if admin user exists
    admin_user = AuthService.get_user_by_email("admin")
    if admin_user:
        print("✅ Admin user already exists")
        print(f"   Email: {admin_user['email']}")
        print(f"   Name: {admin_user['name']}")
        print(f"   Admin: {admin_user['is_admin']}")
    else:
        print("Creating admin user...")
        admin_user = AuthService.create_user(
            email="admin",
            name="Admin User",
            password="admin123", 
            is_admin=True
        )
        if admin_user:
            print("✅ Admin user created successfully")
        else:
            print("❌ Failed to create admin user")
    
    # Test login
    print("Testing login...")
    login_result = AuthService.login_user("admin", "admin123")
    if login_result:
        print("✅ Login test successful!")
        print(f"   Token starts with: {login_result['access_token'][:20]}...")
    else:
        print("❌ Login test failed")
    
    cur.close()
    conn.close()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()