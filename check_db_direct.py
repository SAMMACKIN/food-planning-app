#!/usr/bin/env python3
"""
Direct database check to see what's in the saved_recipes table
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Database connection
DB_URL = "postgresql://postgres:whbutb2012@localhost:5432/food_planning_dev"

def check_database():
    """Check database contents directly"""
    try:
        print("🔍 Connecting to database...")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'saved_recipes'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📊 saved_recipes table exists: {table_exists}")
        
        if table_exists:
            # Check all recipes
            cursor.execute("SELECT COUNT(*) FROM saved_recipes;")
            count = cursor.fetchone()[0]
            print(f"📊 Total recipes in database: {count}")
            
            if count > 0:
                # Show first 10 recipes
                cursor.execute("""
                    SELECT id, user_id, name, created_at 
                    FROM saved_recipes 
                    ORDER BY created_at DESC 
                    LIMIT 10;
                """)
                recipes = cursor.fetchall()
                print(f"📋 Recent recipes:")
                for recipe in recipes:
                    print(f"  - ID: {recipe[0]}")
                    print(f"    User ID: {recipe[1]} (type: {type(recipe[1])})")
                    print(f"    Name: {recipe[2]}")
                    print(f"    Created: {recipe[3]}")
                    print("---")
        
        # Check users table
        cursor.execute("SELECT id, email FROM users ORDER BY created_at DESC LIMIT 5;")
        users = cursor.fetchall()
        print(f"👥 Recent users:")
        for user in users:
            print(f"  - ID: {user[0]} (type: {type(user[0])})")
            print(f"    Email: {user[1]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()