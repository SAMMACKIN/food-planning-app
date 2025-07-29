#!/usr/bin/env python3
import subprocess
import os

os.chdir('/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app')

# Git add
subprocess.run(['git', 'add', '-A'])

# Git commit
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

# Git push
subprocess.run(['git', 'push', 'origin', 'preview'])

print("Changes committed and pushed to preview branch")