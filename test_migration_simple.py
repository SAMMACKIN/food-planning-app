#!/usr/bin/env python3
import os
import sys

# Add backend to path
backend_path = "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend"
sys.path.insert(0, backend_path)

# Set testing environment
os.environ['TESTING'] = 'true'

try:
    print("🧪 Testing migration components...")
    
    # Test 1: Config loading
    print("1. Testing config loading...")
    from app.core.config import get_settings
    settings = get_settings()
    print(f"   ✅ Database URL: {settings.DATABASE_URL}")
    print(f"   ✅ Environment: {settings.ENVIRONMENT}")
    
    # Test 2: Database service
    print("2. Testing database service...")
    from app.core.database_service import db_service
    print(f"   ✅ Using SQLite: {db_service.use_sqlite}")
    print(f"   ✅ Service initialized")
    
    # Test 3: Database connection
    print("3. Testing database connection...")
    from app.core.database_service import test_db_connection
    if test_db_connection():
        print("   ✅ Database connection successful")
    else:
        print("   ❌ Database connection failed")
        sys.exit(1)
    
    # Test 4: Initialize database
    print("4. Testing database initialization...")
    from app.core.database_service import init_db
    init_db()
    print("   ✅ Database initialized")
    
    # Test 5: Auth service
    print("5. Testing auth service...")
    from app.core.auth_service import AuthService
    
    # Try to register a user
    result = AuthService.register_user("test@example.com", "Test User", "password123")
    if result:
        print("   ✅ User registration successful")
        print(f"   ✅ Token created: {len(result['access_token'])} chars")
        
        # Test login
        login_result = AuthService.login_user("test@example.com", "password123")
        if login_result:
            print("   ✅ User login successful")
        else:
            print("   ❌ User login failed")
            sys.exit(1)
    else:
        print("   ❌ User registration failed")
        sys.exit(1)
    
    print("\n🎉 All migration tests passed!")
    print("🚀 Ready to start localhost servers!")
    
except Exception as e:
    print(f"❌ Migration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)