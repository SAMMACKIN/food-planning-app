#!/bin/bash

# Food Planning App Development Starter Script

set -e  # Exit on any error

PROJECT_ROOT="/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"

echo "🚀 Starting Food Planning App Development Environment..."

# Kill existing processes on our ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

sleep 2

# Start backend
echo "🔧 Starting FastAPI backend on port 8001..."
cd "$PROJECT_ROOT/backend"
python simple_app.py > simple_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting React frontend on port 3000..."
cd "$PROJECT_ROOT/frontend"
npm start > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to compile
echo "⏳ Waiting for frontend to compile..."
sleep 10

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend started successfully"
else
    echo "❌ Frontend failed to start"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 Development environment ready!"
echo "   📱 Frontend: http://localhost:3000"
echo "   🔧 Backend API: http://localhost:8001"
echo "   📚 API Docs: http://localhost:8001/docs"
echo ""
echo "💡 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "🔍 Logs:"
echo "   Backend: tail -f $PROJECT_ROOT/backend/simple_backend.log"
echo "   Frontend: tail -f $PROJECT_ROOT/frontend/frontend.log"

# Keep script running and show process IDs
echo $BACKEND_PID > "$PROJECT_ROOT/.backend_pid"
echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend_pid"

echo "Process IDs saved. Services are running in background."