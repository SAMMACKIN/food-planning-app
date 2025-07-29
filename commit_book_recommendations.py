#!/usr/bin/env python3
import subprocess
import os

# Change to the project directory
os.chdir('/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app')

# Git add
subprocess.run(['git', 'add', 'backend/app/services/book_recommendation_service.py'])
subprocess.run(['git', 'add', 'frontend/src/pages/Books/BookRecommendations.tsx'])

# Git commit
commit_message = """Fix AI book recommendations

- Fix AI service import path in book_recommendation_service.py
- Add proper error handling for missing AI service
- Update BookRecommendations component to use proper API utility
- Use recommendationsApi instance with 5-minute timeout for AI requests
- Add AI provider availability testing
- Improve error messages for better user feedback
- Add clear empty state when AI service is unavailable

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

subprocess.run(['git', 'commit', '-m', commit_message])

# Git push
subprocess.run(['git', 'push', 'origin', 'preview'])

print("Changes committed and pushed to preview branch")