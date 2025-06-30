#!/usr/bin/env python3
import os
import sys

# Add backend to Python path
backend_path = '/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend'
sys.path.insert(0, backend_path)
os.chdir(backend_path)
os.environ['TESTING'] = 'true'

# Import and execute the test file
if __name__ == "__main__":
    exec(open('test_startup_fixed.py').read())