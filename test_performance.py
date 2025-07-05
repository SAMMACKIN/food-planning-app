#!/usr/bin/env python3
"""
Test performance improvements for saved recipes
"""
import requests
import time
import json

API_BASE = "http://localhost:8001/api/v1"

def test_performance():
    """Test recipe retrieval performance"""
    # Login
    login_data = {"email": "debug_userid_test@test.com", "password": "test123"}
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing recipe retrieval performance...")
    
    # Test original endpoint
    print("\n📊 Testing original endpoint:")
    start = time.time()
    response = requests.get(f"{API_BASE}/recipes", headers=headers)
    original_time = time.time() - start
    
    if response.status_code == 200:
        recipes = response.json()
        print(f"✅ Original: {original_time:.4f}s for {len(recipes)} recipes")
    else:
        print(f"❌ Original failed: {response.status_code}")
        return
    
    # Test optimized endpoint
    print("\n🚀 Testing optimized endpoint:")
    start = time.time()
    response = requests.get(f"{API_BASE}/recipes-perf/optimized", headers=headers)
    optimized_time = time.time() - start
    
    if response.status_code == 200:
        recipes = response.json()
        print(f"✅ Optimized: {optimized_time:.4f}s for {len(recipes)} recipes")
    else:
        print(f"❌ Optimized failed: {response.status_code} - {response.text}")
        optimized_time = None
    
    # Test fast endpoint
    print("\n⚡ Testing fast endpoint:")
    start = time.time()
    response = requests.get(f"{API_BASE}/recipes-perf/fast", headers=headers)
    fast_time = time.time() - start
    
    if response.status_code == 200:
        recipes = response.json()
        print(f"✅ Fast: {fast_time:.4f}s for {len(recipes)} recipes")
    else:
        print(f"❌ Fast failed: {response.status_code} - {response.text}")
        fast_time = None
    
    # Test performance comparison endpoint
    print("\n📈 Testing performance comparison:")
    response = requests.get(f"{API_BASE}/recipes-perf/performance-test", headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        print(f"📊 Performance comparison results:")
        print(json.dumps(results, indent=2))
    else:
        print(f"❌ Performance test failed: {response.status_code}")
    
    # Calculate improvements
    if original_time > 0:
        optimized_improvement = original_time / optimized_time if optimized_time > 0 else 0
        fast_improvement = original_time / fast_time if fast_time > 0 else 0
        
        print(f"\n🎉 Performance Improvements:")
        print(f"  Optimized endpoint: {optimized_improvement:.1f}x faster")
        print(f"  Fast endpoint: {fast_improvement:.1f}x faster")

if __name__ == "__main__":
    test_performance()