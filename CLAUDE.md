# Food Planning App - Claude Development Guide

## Project Overview
A comprehensive meal planning application with React frontend and FastAPI backend.

## Development Commands

### Frontend (React)
- **Start**: `cd frontend && npm start`
- **Build**: `cd frontend && npm run build` 
- **Test**: `cd frontend && npm test`

### Backend (FastAPI)
- **Start**: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
- **Test**: `cd backend && python -m pytest`
- **Legacy Start**: `cd backend && python simple_app.py` (deprecated - use modular app above)

### Database
- **Location**: `backend/simple_food_app.db` (SQLite)
- **Reset**: Delete the .db file and restart backend

## Current Status
- ✅ Frontend running on http://localhost:3000
- ✅ Backend running on http://localhost:8001  
- ✅ Authentication system working
- ✅ User registration and login functional
- ✅ JWT token management implemented
- ✅ Claude AI integration working
- ✅ AI-powered meal recommendations functional
- ✅ Pantry management system working
- ✅ Family member management working

## Architecture
- **Frontend**: React 18 + TypeScript + Material-UI + Zustand
- **Backend**: FastAPI + SQLite + JWT authentication
- **API**: RESTful endpoints with CORS enabled

## Environment Variables
- Frontend: REACT_APP_API_URL=http://localhost:8001
- Backend: Uses SQLite (no external dependencies needed)

## AI Provider API Keys
The app supports multiple AI providers for meal recommendations. Add at least one API key to the backend/.env file:

### Perplexity AI (Recommended)
- Get your API key from: https://www.perplexity.ai/settings/api
- Add to .env: `PERPLEXITY_API_KEY=your_key_here`
- Model used: llama-3.1-sonar-small-128k-online

### Claude AI 
- Get your API key from: https://console.anthropic.com/
- Add to .env: `ANTHROPIC_API_KEY=your_key_here`
- Model used: claude-3-haiku-20240307

### Groq (Llama models)
- Get your API key from: https://console.groq.com/keys
- Add to .env: `GROQ_API_KEY=your_key_here`
- Model used: llama-3.1-8b-instant

**Note**: The app will automatically detect which providers are available based on configured API keys.

## Next Features to Implement
1. Family member management
2. Ingredient/pantry system  
3. Meal recommendations with Claude API
4. Weekly meal planning
5. Shopping list generation

## Common Issues
- If registration fails, check browser console for debug logs
- Ensure both frontend (3000) and backend (8001) are running
- Backend logs are in `backend/simple_backend.log`

## 🚨 DEPLOYMENT WORKFLOW - ABSOLUTE CRITICAL RULE 🚨
⚠️ **NEVER DEPLOY DIRECTLY TO PRODUCTION WITHOUT EXPLICIT USER APPROVAL** ⚠️
⚠️ **CLAUDE MUST ALWAYS USE PREVIEW-FIRST WORKFLOW** ⚠️
⚠️ **USER MUST EXPLICITLY SAY "DEPLOY TO PRODUCTION" BEFORE ANY PRODUCTION DEPLOYMENT** ⚠️

### 🛑 CRITICAL DEPLOYMENT VIOLATIONS TO AVOID:
- ❌ NEVER run commands like `git push origin master` without explicit user approval
- ❌ NEVER run commands like `git checkout master && git merge preview` without user saying "deploy to production"
- ❌ NEVER assume user wants production deployment
- ❌ NEVER deploy to production just because preview works

### MANDATORY Steps for ALL Changes (NO EXCEPTIONS):
1. **Work on preview branch ONLY**: `git checkout preview`
2. **Commit to preview**: `git add . && git commit -m "..."`
3. **Push to preview ONLY**: `git push origin preview` 
4. **Test on preview environment**: https://food-planning-app-preview.up.railway.app/
5. **STOP AND WAIT**: Do NOT touch production until user explicitly approves
6. **Only after user says "deploy to production"**: `git checkout master && git merge preview && git push origin master`

### 🛑 CLAUDE DEPLOYMENT RULES:
- ❌ NEVER push directly to master branch without explicit approval
- ❌ NEVER deploy to production without user testing preview first
- ❌ NEVER assume user approval - wait for explicit "deploy to production" command
- ❌ NEVER merge to master automatically
- ✅ ALWAYS work on preview branch
- ✅ ALWAYS let user test preview environment first
- ✅ ALWAYS wait for user to explicitly say "deploy to production" or "push to production"
- ✅ ALWAYS ask "Should I deploy this to production?" if uncertain

### 🆘 IF CLAUDE ACCIDENTALLY DEPLOYS TO PRODUCTION:
1. Immediately revert production: `git checkout master && git reset --hard HEAD~1 && git push origin master --force`
2. Apologize to user
3. Confirm preview branch still has the changes
4. Wait for explicit approval before any future production deployments

### 🛑 CLAUDE TESTING RULES:

1. **Test Scope and Structure**
   - Create one test file per source file, with matching folder structure.
   - Name test files clearly (e.g. `test_create_order.py` for `create_order.py`).
   - Write focused, readable tests that check a single behaviour or outcome.

2. **Test Content**
   - Cover:
     - Normal/happy path
     - Edge cases
     - Invalid inputs and expected errors
   - Use real data types and meaningful inputs, not generic placeholders.
   - Write descriptive test function names (e.g. `test_returns_error_on_invalid_quantity`).

3. **Coverage and Assertions**
   - Ensure all new code is covered by tests unless explicitly excluded.
   - Focus on logical paths and business-critical logic.
   - Use clear, specific assertions (e.g. `assert response.status == "confirmed"` not just `assert response`).
   - Avoid over-mocking — prefer testing real behaviour when practical.

4. **Maintainability**
   - Keep tests short, isolated, and fast.
   - Reuse setup with fixtures or factories where helpful, but don’t over-abstract.
   - When code is refactored, update or regenerate the corresponding tests.
   - When code is deleted, remove obsolete tests.

5. **CI Compatibility**
   - All test code should be runnable via CLI using the designated test runner (e.g. `pytest`, `jest`, `vitest`).
   - Generated tests must not rely on local-only state or environments unless clearly noted.

6. **Test Naming and Reporting**
   - Make test names self-explanatory. Avoid comments explaining what a test does — the name should make it obvious.
   - Ensure failing tests provide meaningful error messages and easy-to-debug failures.

7. **Test Output Format**
   - Do not inline test code with production code.
   - Place tests in a separate `tests/` folder with the same structure as the `src/` folder.

Always regenerate or update tests when code is changed. Do not write or return new code without corresponding test coverage unless explicitly told to.



### Preview Environment URLs:
- **Frontend Preview**: https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app
- **Backend Preview**: https://food-planning-app-preview.up.railway.app/

### Production Environment URLs:
- **Frontend Production**: https://food-planning-app.vercel.app
- **Backend Production**: https://food-planning-app-production.up.railway.app/

## Development Notes
- Hot reload enabled for both frontend and backend
- Debug logging added to API calls
- CORS configured for localhost development
- SQLite database auto-creates on first run