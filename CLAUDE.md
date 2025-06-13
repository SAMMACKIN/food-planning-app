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

## Development Notes
- Hot reload enabled for both frontend and backend
- Debug logging added to API calls
- CORS configured for localhost development
- SQLite database auto-creates on first run