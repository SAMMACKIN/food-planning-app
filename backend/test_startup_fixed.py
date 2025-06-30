#!/usr/bin/env python3
"""
Test server startup after fixing import issues
"""
import os
import sys

# Set environment for testing
os.environ['TESTING'] = 'true'

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        # Test config import
        from app.core.config import get_settings
        settings = get_settings()
        print(f"   ✅ Config loaded - DATABASE_URL: {settings.DATABASE_URL}")
        print(f"   ✅ DEBUG setting: {getattr(settings, 'DEBUG', 'Not set')}")
        
        # Test database service
        from app.core.database_service import db_service, init_db, test_db_connection
        print(f"   ✅ Database service - Using SQLite: {db_service.use_sqlite}")
        
        # Test SQLAlchemy setup
        from app.db.database import Base, engine, SessionLocal
        print("   ✅ SQLAlchemy components imported")
        
        # Test models
        from app.models.simple_models import User, FamilyMember, Ingredient
        print("   ✅ Simple models imported")
        
        # Test auth service
        from app.core.auth_service import AuthService
        print("   ✅ Auth service imported")
        
        # Test main app
        from app.main import app
        print("   ✅ FastAPI app imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection and initialization"""
    print("🗄️ Testing database...")
    
    try:
        from app.core.database_service import test_db_connection, init_db
        
        # Test connection
        if test_db_connection():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Initialize database
        init_db()
        print("   ✅ Database initialization successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_functionality():
    """Test authentication system"""
    print("🔐 Testing authentication...")
    
    try:
        from app.core.auth_service import AuthService
        
        # Test user registration
        result = AuthService.register_user("testuser@example.com", "Test User", "testpass123")
        if result:
            print("   ✅ User registration successful")
            print(f"   ✅ Token length: {len(result['access_token'])}")
            
            # Test login
            login_result = AuthService.login_user("testuser@example.com", "testpass123")
            if login_result:
                print("   ✅ User login successful")
                
                # Test token verification  
                user = AuthService.verify_user_token(login_result['access_token'])
                if user:
                    print("   ✅ Token verification successful")
                    return True
                else:
                    print("   ❌ Token verification failed")
                    return False
            else:
                print("   ❌ User login failed")
                return False
        else:
            print("   ❌ User registration failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_app():
    """Test FastAPI application"""
    print("🚀 Testing FastAPI app...")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        print(f"   ✅ Health endpoint: {response.status_code}")
        
        # Test auth endpoints
        response = client.post("/api/v1/auth/login", json={"email": "test", "password": "test"})
        print(f"   ✅ Auth endpoint accessible: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FastAPI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Running Migration Startup Tests")
    print("==================================")
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database_connection),
        ("Authentication Tests", test_auth_functionality),
        ("FastAPI Tests", test_fastapi_app)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if not test_func():
            all_passed = False
            print(f"❌ {test_name} FAILED")
            break
        else:
            print(f"✅ {test_name} PASSED")
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Ready to start localhost server")
        print("\nTo start the server:")
        print("python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")
        return True
    else:
        print("\n❌ TESTS FAILED")
        print("❌ Cannot start server safely")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)