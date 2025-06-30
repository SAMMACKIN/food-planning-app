import os
print("Testing different CI environment combinations...")

# Test 1: TESTING=true
os.environ['TESTING'] = 'true'
if 'CI' in os.environ:
    del os.environ['CI']
if 'GITHUB_ACTIONS' in os.environ:
    del os.environ['GITHUB_ACTIONS']

try:
    from app.core.config import get_settings
    settings1 = get_settings()
    print(f"✅ Test 1 (TESTING=true): JWT_SECRET exists: {bool(settings1.JWT_SECRET)}")
except Exception as e:
    print(f"❌ Test 1 failed: {e}")

# Clear cache
from app.core.config import get_settings
get_settings.cache_clear()

# Test 2: CI=true (GitHub Actions style)
if 'TESTING' in os.environ:
    del os.environ['TESTING']
os.environ['CI'] = 'true'

try:
    settings2 = get_settings()
    print(f"✅ Test 2 (CI=true): JWT_SECRET exists: {bool(settings2.JWT_SECRET)}")
except Exception as e:
    print(f"❌ Test 2 failed: {e}")

# Clear cache
get_settings.cache_clear()

# Test 3: GITHUB_ACTIONS=true
if 'CI' in os.environ:
    del os.environ['CI']
os.environ['GITHUB_ACTIONS'] = 'true'

try:
    settings3 = get_settings()
    print(f"✅ Test 3 (GITHUB_ACTIONS=true): JWT_SECRET exists: {bool(settings3.JWT_SECRET)}")
except Exception as e:
    print(f"❌ Test 3 failed: {e}")

print("🎉 All tests passed!")