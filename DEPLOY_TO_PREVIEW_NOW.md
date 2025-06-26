# 🚀 Deploy Database Fixes to Preview - Run These Commands Now

## Step 1: Navigate to Project Directory
```bash
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"
```

## Step 2: Check Current Status
```bash
git status
```

## Step 3: Stage All Database Fix Files
```bash
git add backend/app/core/database.py
git add backend/app/api/recipes.py  
git add backend/app/main.py
git add frontend/src/components/Recipe/RecipeDebugPanel.tsx
git add frontend/src/pages/Recommendations/MealRecommendations.tsx
git add backend/debug_database.py
git add DATABASE_FIXES_SUMMARY.md
git add backend/deploy_database_fixes.sh
git add DEPLOYMENT_COMMANDS.md
git add DEPLOY_TO_PREVIEW_NOW.md
```

## Step 4: Create Commit
```bash
git commit -m "$(cat <<'EOF'
Fix critical database operations for recipe functionality

## Critical Fixes:
- Enhanced database connection handling with proper error checking
- Implemented atomic transactions with rollback on failures  
- Strengthened authentication token validation
- Added comprehensive error handling for recipes, ratings, and meal plans
- Created health check endpoint for diagnostics
- Enhanced debug panel with real-time system status

## Technical Changes:
- database.py: Added schema verification, improved transactions, enhanced connection handling
- recipes.py: Hardened all endpoints with proper validation and error handling
- RecipeDebugPanel.tsx: Added system health checks and better diagnostics
- MealRecommendations.tsx: Fixed JSX syntax errors for Vercel build

## Issues Resolved:
- Recipe saving failures
- Recipe rating functionality not working
- Adding recipes to meal plans failing
- Poor error messages masking root causes
- Database connection instability

Fixes: Recipe saving, rating, and meal plan operations now work reliably

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Step 5: Deploy to Preview
```bash
git push origin preview
```

## Step 6: Test Preview Environment
Once deployed, test at:
- **Frontend**: https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app
- **Backend Health**: https://food-planning-app-preview.up.railway.app/api/v1/recipes/debug/health

## Step 7: Test Recipe Functionality
1. Log into preview app
2. Try saving a recipe recommendation  
3. Try rating a saved recipe
4. Try adding a recipe to meal plan
5. If errors occur, check the enhanced debug panel

## What's Being Deployed:
✅ **Enhanced Database Handling** - Proper transactions and error handling
✅ **Authentication Fixes** - Better token validation and error reporting  
✅ **Recipe API Hardening** - Robust save/rate/meal-plan operations
✅ **Debug Tools** - Health endpoint and enhanced error diagnostics
✅ **JSX Syntax Fixes** - Vercel build compatibility

**Run these commands now to deploy the fixes to preview!**