#!/usr/bin/env python3
"""
Test the exact query that's failing
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Database connection
DB_URL = "postgresql://postgres:whbutb2012@localhost:5432/food_planning_dev"

def test_query():
    """Test the exact query from the API"""
    try:
        print("🔍 Connecting to database...")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Test with the exact user_id from our debug test
        user_id = "974de73c-dd06-4910-a9d2-7dcc6d413bd0"
        print(f"🔍 Testing with user_id: {user_id}")
        
        # Test the exact query from the API
        query = '''
            SELECT r.id, r.user_id, r.name, r.description, r.prep_time, r.difficulty,
                   r.servings, r.ingredients_needed, r.instructions
            FROM saved_recipes r
            WHERE r.user_id = %s
            ORDER BY r.updated_at DESC
        '''
        
        print(f"🔍 Running query: {query}")
        print(f"🔍 With parameter: {user_id}")
        
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        print(f"📊 Query returned {len(results)} results")
        
        if len(results) > 0:
            print("✅ Query works! Results:")
            for i, result in enumerate(results):
                print(f"  {i+1}. ID: {result[0]}")
                print(f"     User ID: {result[1]}")
                print(f"     Name: {result[2]}")
        else:
            print("❌ Query returned no results")
            
            # Test alternative queries
            print("🔍 Testing alternative queries...")
            
            # Test with LIKE
            cursor.execute("SELECT id, user_id, name FROM saved_recipes WHERE user_id LIKE %s", (f"%{user_id}%",))
            like_results = cursor.fetchall()
            print(f"📊 LIKE query returned {len(like_results)} results")
            
            # Test without WHERE clause
            cursor.execute("SELECT id, user_id, name FROM saved_recipes")
            all_results = cursor.fetchall()
            print(f"📊 All recipes query returned {len(all_results)} results")
            
            # Check if our user_id exists in the results
            for result in all_results:
                if str(result[1]) == user_id:
                    print(f"✅ Found matching user_id: {result[1]} == {user_id}")
                    break
            else:
                print(f"❌ User_id {user_id} not found in any results")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query()