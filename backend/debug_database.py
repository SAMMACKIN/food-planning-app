#!/usr/bin/env python3
"""
Database debugging script to identify and fix database issues
"""
import sqlite3
import os
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_database_files():
    """List all database files in the backend directory"""
    db_files = []
    for file in os.listdir('.'):
        if file.endswith('.db'):
            stat = os.stat(file)
            db_files.append({
                'name': file,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime)
            })
    return db_files

def inspect_database_schema(db_path):
    """Inspect database schema and contents"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_info = {'tables': {}}
        
        for table in tables:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            
            schema_info['tables'][table] = {
                'columns': [{'name': col[1], 'type': col[2], 'nullable': not col[3]} for col in columns],
                'row_count': count
            }
        
        conn.close()
        return schema_info
        
    except Exception as e:
        return {'error': str(e)}

def test_database_operations(db_path):
    """Test basic database operations"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test if we can read from key tables
        tests = {}
        
        # Test users table
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            tests['users_readable'] = True
            tests['users_count'] = cursor.fetchone()[0]
        except Exception as e:
            tests['users_readable'] = False
            tests['users_error'] = str(e)
        
        # Test saved_recipes table
        try:
            cursor.execute("SELECT COUNT(*) FROM saved_recipes")
            tests['recipes_readable'] = True
            tests['recipes_count'] = cursor.fetchone()[0]
        except Exception as e:
            tests['recipes_readable'] = False
            tests['recipes_error'] = str(e)
        
        # Test meal_plans table
        try:
            cursor.execute("SELECT COUNT(*) FROM meal_plans")
            tests['meal_plans_readable'] = True
            tests['meal_plans_count'] = cursor.fetchone()[0]
        except Exception as e:
            tests['meal_plans_readable'] = False
            tests['meal_plans_error'] = str(e)
        
        # Test recipe_ratings table
        try:
            cursor.execute("SELECT COUNT(*) FROM recipe_ratings")
            tests['ratings_readable'] = True
            tests['ratings_count'] = cursor.fetchone()[0]
        except Exception as e:
            tests['ratings_readable'] = False
            tests['ratings_error'] = str(e)
        
        conn.close()
        return tests
        
    except Exception as e:
        return {'connection_error': str(e)}

def main():
    """Main debugging function"""
    print("🔍 Database Debugging Report")
    print("=" * 50)
    
    # List all database files
    db_files = list_database_files()
    print(f"\n📁 Found {len(db_files)} database files:")
    for db in db_files:
        print(f"  - {db['name']}: {db['size']} bytes, modified: {db['modified']}")
    
    # Inspect each database
    for db in db_files:
        print(f"\n🔍 Inspecting {db['name']}:")
        print("-" * 30)
        
        schema = inspect_database_schema(db['name'])
        if 'error' in schema:
            print(f"  ❌ Error: {schema['error']}")
            continue
        
        print(f"  📊 Tables found: {len(schema['tables'])}")
        for table_name, table_info in schema['tables'].items():
            print(f"    - {table_name}: {table_info['row_count']} rows, {len(table_info['columns'])} columns")
        
        # Test operations
        tests = test_database_operations(db['name'])
        print(f"  🧪 Operation Tests:")
        for test_name, result in tests.items():
            if test_name.endswith('_readable'):
                status = "✅" if result else "❌"
                print(f"    {status} {test_name.replace('_readable', '')}: {result}")
            elif test_name.endswith('_count'):
                print(f"      Count: {result}")
            elif test_name.endswith('_error'):
                print(f"      Error: {result}")
    
    # Check environment configuration
    print(f"\n🌍 Environment Check:")
    print(f"  ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"  RAILWAY_DEPLOYMENT_ID: {os.getenv('RAILWAY_DEPLOYMENT_ID', 'None')}")
    print(f"  DB_PATH: {os.getenv('DB_PATH', 'None')}")
    
    # Determine which database should be used
    from app.core.config import get_settings
    settings = get_settings()
    expected_db = settings.DB_PATH
    print(f"  Expected DB path: {expected_db}")
    
    if os.path.exists(expected_db):
        print(f"  ✅ Expected database exists")
    else:
        print(f"  ❌ Expected database does not exist!")
    
    print(f"\n🏁 Debugging complete")

if __name__ == "__main__":
    main()