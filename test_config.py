#!/usr/bin/env python3
"""
Test configuration loading to debug CI issues
"""
import os
import sys
sys.path.insert(0, 'backend')

# Set test environment
os.environ['TESTING'] = 'true'

try:
    from backend.app.core.config import get_settings
    
    print("Testing configuration loading...")
    settings = get_settings()
    
    print(f"✅ JWT_SECRET: {settings.JWT_SECRET[:20]}..." if settings.JWT_SECRET else "❌ JWT_SECRET is None")
    print(f"✅ ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"✅ DB_PATH: {settings.DB_PATH}")
    print(f"✅ CORS_ORIGINS: {len(settings.CORS_ORIGINS)} origins")
    
    print("\n🎉 Configuration loaded successfully!")
    
except Exception as e:
    print(f"❌ Configuration loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)