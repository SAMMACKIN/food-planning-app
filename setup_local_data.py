#!/usr/bin/env python3
"""
Set up local database with sample data for development
"""
import requests
import json

def setup_local_data():
    base_url = "http://localhost:8001/api/v1"
    
    print("🔧 Setting up local database with sample data...")
    
    # Login and get token
    login_data = {"email": "admin", "password": "admin123"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Logged in successfully")
    
    # 1. Create family members
    print("\n📨 Creating family members...")
    family_members = [
        {
            "name": "John Admin", 
            "age": 35,
            "dietary_restrictions": ["Gluten-Free"],
            "preferences": {
                "food_likes": "Italian food, grilled vegetables",
                "food_dislikes": "Spicy food",
                "preferred_cuisines": ["Italian", "Mediterranean"]
            }
        },
        {
            "name": "Jane Smith",
            "age": 32, 
            "dietary_restrictions": ["Vegetarian"],
            "preferences": {
                "food_likes": "Pasta, salads, fresh fruits",
                "food_dislikes": "Mushrooms",
                "preferred_cuisines": ["Italian", "Indian", "Thai"]
            }
        },
        {
            "name": "Emma Smith",
            "age": 8,
            "dietary_restrictions": [],
            "preferences": {
                "food_likes": "Pizza, chicken nuggets, fruits",
                "food_dislikes": "Vegetables, fish",
                "preferred_cuisines": ["American", "Italian"]
            }
        }
    ]
    
    for member in family_members:
        try:
            response = requests.post(f"{base_url}/family/members", json=member, headers=headers)
            if response.status_code in [200, 201]:
                print(f"  ✅ Created: {member['name']}")
            else:
                print(f"  ❌ Failed to create {member['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {member['name']}: {e}")
    
    # 2. Add pantry items
    print("\n🥫 Adding pantry items...")
    pantry_items = [
        {"ingredient_id": "chicken-breast", "quantity": 2.0},
        {"ingredient_id": "olive-oil", "quantity": 1.0},
        {"ingredient_id": "pasta", "quantity": 3.0},
        {"ingredient_id": "tomatoes", "quantity": 5.0},
        {"ingredient_id": "onions", "quantity": 3.0},
        {"ingredient_id": "garlic", "quantity": 10.0},
        {"ingredient_id": "cheese", "quantity": 8.0},
        {"ingredient_id": "eggs", "quantity": 12.0},
        {"ingredient_id": "milk", "quantity": 2.0},
        {"ingredient_id": "bread", "quantity": 2.0},
        {"ingredient_id": "broccoli", "quantity": 1.0},
        {"ingredient_id": "carrots", "quantity": 4.0},
        {"ingredient_id": "spinach", "quantity": 2.0},
        {"ingredient_id": "white-rice", "quantity": 2.0},
        {"ingredient_id": "salmon", "quantity": 1.5}
    ]
    
    for item in pantry_items:
        try:
            response = requests.post(f"{base_url}/pantry", json=item, headers=headers)
            if response.status_code in [200, 201]:
                print(f"  ✅ Added: {item['ingredient_id']} ({item['quantity']} units)")
            else:
                print(f"  ❌ Failed to add {item['ingredient_id']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error adding {item['ingredient_id']}: {e}")
    
    # 3. Test recommendations
    print("\n🤖 Testing recommendations...")
    try:
        rec_data = {
            "num_recommendations": 3,
            "ai_provider": "claude"  # Try Claude first
        }
        response = requests.post(f"{base_url}/recommendations", json=rec_data, headers=headers)
        if response.status_code == 200:
            recommendations = response.json()
            print(f"  ✅ Generated {len(recommendations)} recommendations")
            for i, rec in enumerate(recommendations[:2], 1):
                print(f"    {i}. {rec['name']}")
        else:
            print(f"  ❌ Recommendations failed: {response.text}")
            # Try with a different AI provider
            rec_data["ai_provider"] = "groq"
            response = requests.post(f"{base_url}/recommendations", json=rec_data, headers=headers)
            if response.status_code == 200:
                recommendations = response.json()
                print(f"  ✅ Generated {len(recommendations)} recommendations with Groq")
    except Exception as e:
        print(f"  ❌ Recommendations error: {e}")
    
    print("\n🎉 Local database setup complete!")
    print("\nYou can now:")
    print("- View family members in Family Management")
    print("- See pantry items in Pantry Management") 
    print("- Generate meal recommendations")
    print("- Save and view recipes")

if __name__ == "__main__":
    setup_local_data()