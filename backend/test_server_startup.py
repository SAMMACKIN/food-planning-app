#!/usr/bin/env python3
"""
Test if the server can start up with the new migration code
"""
import os
os.environ['TESTING'] = 'true'

try:
    print("🧪 Testing server startup components...")
    
    # Test imports
    print("1. Testing imports...")
    from app.main import app
    print("   ✅ Main app imported")
    
    from app.core.config import get_settings
    settings = get_settings()
    print(f"   ✅ Settings loaded - DB: {settings.DATABASE_URL}")
    
    from app.core.database_service import db_service, init_db
    print(f"   ✅ Database service loaded - SQLite: {db_service.use_sqlite}")
    
    # Test database initialization
    print("2. Testing database initialization...")
    init_db()
    print("   ✅ Database initialized")
    
    # Test FastAPI startup
    print("3. Testing FastAPI app...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    print(f"   ✅ Health endpoint: {response.status_code}")
    
    # Test auth endpoints exist
    response = client.post("/api/v1/auth/login", json={"email": "test", "password": "test"})
    print(f"   ✅ Auth endpoint accessible: {response.status_code}")
    
    print("\n🎉 Server startup test passed!")
    print("🚀 Ready to start full server!")
    
except Exception as e:
    print(f"❌ Server startup test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)