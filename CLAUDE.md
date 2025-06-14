# Food Planning App - Claude Development Guide

## Project Overview
A comprehensive meal planning application with React frontend and FastAPI backend.

## Development Commands

### Frontend (React)
- **Start**: `cd frontend && npm start`
- **Build**: `cd frontend && npm run build` 
- **Test**: `cd frontend && npm test`

### Backend (FastAPI)
- **Start**: `cd backend && python simple_app.py`
- **Test**: `cd backend && python -m pytest`

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
⚠️ **NEVER DEPLOY DIRECTLY TO PRODUCTION WITHOUT PREVIEW TESTING** ⚠️
⚠️ **CLAUDE MUST ALWAYS USE PREVIEW-FIRST WORKFLOW** ⚠️
⚠️ **USER MUST APPROVE ALL CHANGES BEFORE PRODUCTION** ⚠️

### MANDATORY Steps for ALL Changes (NO EXCEPTIONS):
1. **Work on preview branch ONLY**: `git checkout preview`
2. **Commit to preview**: `git add . && git commit -m "..."`
3. **Push to preview**: `git push origin preview` 
4. **Test on preview environment**: https://food-planning-app-preview.up.railway.app/
5. **WAIT for user approval**: User must test and explicitly approve changes
6. **Only after approval**: `git checkout master && git merge preview && git push origin master`

### 🛑 CLAUDE DEPLOYMENT RULES:
- ❌ NEVER push directly to master branch
- ❌ NEVER deploy to production without user testing preview first
- ❌ NEVER assume user approval - wait for explicit confirmation
- ✅ ALWAYS work on preview branch
- ✅ ALWAYS let user test preview environment first
- ✅ ALWAYS wait for user to say "deploy to production"

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