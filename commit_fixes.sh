#!/bin/bash
cd "$(dirname "$0")"
git add -A
git commit -m "Fix multiple TypeScript and Material-UI issues for Vercel build

- Change favoriteFilter from boolean|'' to string type
- Update favoriteFilter logic to handle string values  
- Fix conditional checks for favoriteFilter
- Remove Box components inside MenuItem (simplify)
- Add missing InputAdornment import
- Fix TextField InputProps to use InputAdornment properly

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin preview
echo "Changes pushed to preview branch"