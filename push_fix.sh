#!/bin/bash
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"
git add -A
git commit -m "Fix JWT_SECRET validation for GitHub Actions CI environment

- Add GITHUB_ACTIONS environment variable detection for CI
- Fix config structure by moving CORS and other settings to __init__
- Ensure CI environment properly falls back to test JWT_SECRET  
- Support both CI=true and GITHUB_ACTIONS=true detection

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin preview