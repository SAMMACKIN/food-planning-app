#!/bin/bash

echo "🎨 Starting Food Planning App Frontend"
echo "======================================"

# Navigate to frontend directory
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/frontend"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8001"
else
    echo "⚠️ Backend is not running on http://localhost:8001"
    echo "💡 Start the backend first with:"
    echo "   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
fi

# Set environment variables for frontend
export REACT_APP_API_URL=http://localhost:8001

# Kill any existing frontend process on port 3000
echo "🛑 Stopping any existing frontend server..."
pkill -f "npm start" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# Wait a moment
sleep 2

# Start the frontend server
echo "🚀 Starting frontend server on http://localhost:3000..."
echo "📋 Environment: REACT_APP_API_URL=$REACT_APP_API_URL"

npm start