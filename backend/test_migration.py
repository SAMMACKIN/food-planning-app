#!/usr/bin/env python3
"""
Test script to verify the database migration works
"""
import os
import sys
sys.path.insert(0, '.')

# Set testing environment
os.environ['TESTING'] = 'true'

from app.core.database_service import db_service, init_db, test_db_connection
from app.core.auth_service import AuthService

def test_database_migration():
    """Test the database migration and authentication system"""
    print("🧪 Testing Database Migration...")
    
    # Test database connection
    print(f"Database backend: {'SQLite' if db_service.use_sqlite else 'PostgreSQL'}")
    print(f"Database URL: {db_service.settings.DATABASE_URL}")
    
    # Test connection
    if not test_db_connection():
        print("❌ Database connection failed")
        return False
    print("✅ Database connection successful")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialization successful")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Test user registration
    try:
        result = AuthService.register_user("test@example.com", "Test User", "testpass123")
        if result:
            print("✅ User registration successful")
            print(f"   User ID: {result['user_id']}")
            print(f"   Token length: {len(result['access_token'])}")
        else:
            print("❌ User registration failed")
            return False
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return False
    
    # Test user login
    try:
        result = AuthService.login_user("test@example.com", "testpass123")
        if result:
            print("✅ User login successful")
            print(f"   Email: {result['email']}")
        else:
            print("❌ User login failed")
            return False
    except Exception as e:
        print(f"❌ User login error: {e}")
        return False
    
    # Test token verification
    try:
        user = AuthService.verify_user_token(result['access_token'])
        if user:
            print("✅ Token verification successful")
            print(f"   User: {user['email']}")
        else:
            print("❌ Token verification failed")
            return False
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        return False
    
    print("\n🎉 All migration tests passed!")
    return True

if __name__ == "__main__":
    success = test_database_migration()
    sys.exit(0 if success else 1)