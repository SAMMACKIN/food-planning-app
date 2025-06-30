#!/bin/bash

echo "🚀 Starting localhost development environment..."

# Set working directory
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"

# Check if backend is already running
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Backend already running on port 8001"
else
    echo "🔧 Starting backend server..."
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
    BACKEND_PID=$!
    echo "✅ Backend started with PID: $BACKEND_PID"
    cd ..
fi

# Wait a moment for backend to start
sleep 3

# Test backend health
echo "🔍 Testing backend health..."
if curl -f http://localhost:8001/health 2>/dev/null; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend health check failed"
fi

# Check if frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Frontend already running on port 3000"
else
    echo "🎨 Starting frontend server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    echo "✅ Frontend started with PID: $FRONTEND_PID"
    cd ..
fi

echo "📱 Development environment ready:"
echo "   Backend:  http://localhost:8001"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8001/docs"

echo "🛑 To stop servers:"
echo "   pkill -f uvicorn"
echo "   pkill -f 'npm start'"