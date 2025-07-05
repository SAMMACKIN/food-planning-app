#!/usr/bin/env python3
"""
Check the database schema to understand UUID types
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Database connection
DB_URL = "postgresql://postgres:whbutb2012@localhost:5432/food_planning_dev"

def check_schema():
    """Check the database schema"""
    try:
        print("🔍 Connecting to database...")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Check the column types for saved_recipes table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'saved_recipes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("📊 saved_recipes table schema:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check users table too
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("👥 users table schema:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
        # Test different query approaches
        user_id = "974de73c-dd06-4910-a9d2-7dcc6d413bd0"
        print(f"\n🔍 Testing different query approaches for user_id: {user_id}")
        
        # Test 1: Direct string comparison
        cursor.execute("SELECT COUNT(*) FROM saved_recipes WHERE user_id = %s", (user_id,))
        count1 = cursor.fetchone()[0]
        print(f"📊 String comparison: {count1} results")
        
        # Test 2: Cast to UUID
        cursor.execute("SELECT COUNT(*) FROM saved_recipes WHERE user_id = %s::uuid", (user_id,))
        count2 = cursor.fetchone()[0]
        print(f"📊 UUID cast: {count2} results")
        
        # Test 3: Cast column to text
        cursor.execute("SELECT COUNT(*) FROM saved_recipes WHERE user_id::text = %s", (user_id,))
        count3 = cursor.fetchone()[0]
        print(f"📊 Column cast to text: {count3} results")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()