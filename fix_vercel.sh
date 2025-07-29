#!/bin/sh
git add -A
git commit -m "Fix TypeScript type issues for Vercel build

- Change favoriteFilter from boolean|'' to string type
- Update favoriteFilter logic to handle string values
- Fix conditional checks for favoriteFilter

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin preview