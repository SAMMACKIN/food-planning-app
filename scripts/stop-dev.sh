#!/bin/bash

# Food Planning App Development Stop Script

PROJECT_ROOT="/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"

echo "🛑 Stopping Food Planning App Development Environment..."

# Kill processes by PID if files exist
if [ -f "$PROJECT_ROOT/.backend_pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/.backend_pid")
    kill $BACKEND_PID 2>/dev/null || true
    rm "$PROJECT_ROOT/.backend_pid"
    echo "✅ Backend stopped (PID: $BACKEND_PID)"
fi

if [ -f "$PROJECT_ROOT/.frontend_pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend_pid")
    kill $FRONTEND_PID 2>/dev/null || true
    rm "$PROJECT_ROOT/.frontend_pid"
    echo "✅ Frontend stopped (PID: $FRONTEND_PID)"
fi

# Also kill by port as backup
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

echo "🧹 All services stopped and ports cleaned up"