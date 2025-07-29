#!/usr/bin/env python3
import subprocess
import os
import sys

# Change to the project directory
os.chdir('/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app')

# Check git status
print("=== Git Status ===")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
print(result.stdout)

if result.stdout.strip():
    print("\n=== Files with changes ===")
    print(result.stdout)
    
    # Show diff for changed files
    print("\n=== Git Diff ===")
    diff_result = subprocess.run(['git', 'diff', '--stat'], capture_output=True, text=True)
    print(diff_result.stdout)
    
    # Ask user if they want to commit
    response = input("\nDo you want to commit and push these changes? (y/n): ")
    
    if response.lower() == 'y':
        # Add all changes
        subprocess.run(['git', 'add', '-A'])
        
        # Commit with message
        commit_message = """Fix multiple TypeScript and Material-UI issues for Vercel build

- Change favoriteFilter from boolean|'' to string type
- Update favoriteFilter logic to handle string values  
- Fix conditional checks for favoriteFilter
- Remove Box components inside MenuItem (simplify)
- Add missing InputAdornment import
- Fix TextField InputProps to use InputAdornment properly

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
        
        subprocess.run(['git', 'commit', '-m', commit_message])
        
        # Push to preview
        print("\nPushing to preview branch...")
        push_result = subprocess.run(['git', 'push', 'origin', 'preview'], capture_output=True, text=True)
        print(push_result.stdout)
        print(push_result.stderr)
        
        print("\nChanges committed and pushed to preview branch!")
else:
    print("No changes to commit.")
    
    # Check current branch
    branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
    print(f"\nCurrent branch: {branch_result.stdout.strip()}")
    
    # Check latest commit
    log_result = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True)
    print(f"Latest commit: {log_result.stdout.strip()}")