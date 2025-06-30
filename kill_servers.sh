#!/bin/bash

echo "🛑 Killing existing development servers..."
echo "========================================"

# Kill processes on port 8001 (backend)
echo "🔧 Checking for processes on port 8001 (backend)..."
BACKEND_PIDS=$(lsof -ti :8001)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "   Found processes: $BACKEND_PIDS"
    echo "   Killing backend processes..."
    kill -9 $BACKEND_PIDS
    echo "   ✅ Backend processes killed"
else
    echo "   ✅ No processes running on port 8001"
fi

# Kill processes on port 3000 (frontend)
echo "🎨 Checking for processes on port 3000 (frontend)..."
FRONTEND_PIDS=$(lsof -ti :3000)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "   Found processes: $FRONTEND_PIDS"
    echo "   Killing frontend processes..."
    kill -9 $FRONTEND_PIDS
    echo "   ✅ Frontend processes killed"
else
    echo "   ✅ No processes running on port 3000"
fi

# Kill any uvicorn processes
echo "🐍 Killing any uvicorn processes..."
UVICORN_PIDS=$(pgrep -f uvicorn)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "   Found uvicorn processes: $UVICORN_PIDS"
    kill -9 $UVICORN_PIDS
    echo "   ✅ Uvicorn processes killed"
else
    echo "   ✅ No uvicorn processes found"
fi

# Kill any npm start processes
echo "📦 Killing any npm start processes..."
NPM_PIDS=$(pgrep -f "npm start")
if [ ! -z "$NPM_PIDS" ]; then
    echo "   Found npm processes: $NPM_PIDS"
    kill -9 $NPM_PIDS
    echo "   ✅ NPM processes killed"
else
    echo "   ✅ No npm start processes found"
fi

# Kill any react-scripts processes
echo "⚛️ Killing any react-scripts processes..."
REACT_PIDS=$(pgrep -f "react-scripts")
if [ ! -z "$REACT_PIDS" ]; then
    echo "   Found react-scripts processes: $REACT_PIDS"
    kill -9 $REACT_PIDS
    echo "   ✅ React-scripts processes killed"
else
    echo "   ✅ No react-scripts processes found"
fi

# Wait a moment for processes to die
echo "⏳ Waiting for processes to terminate..."
sleep 3

# Final check
echo "🔍 Final port check..."
REMAINING_8001=$(lsof -ti :8001)
REMAINING_3000=$(lsof -ti :3000)

if [ -z "$REMAINING_8001" ] && [ -z "$REMAINING_3000" ]; then
    echo "✅ All processes successfully killed!"
    echo "🚀 Ports 3000 and 8001 are now free"
    echo ""
    echo "Ready to start fresh servers:"
    echo "   Backend:  cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
    echo "   Frontend: cd frontend && npm start"
else
    if [ ! -z "$REMAINING_8001" ]; then
        echo "⚠️ Port 8001 still occupied by: $REMAINING_8001"
    fi
    if [ ! -z "$REMAINING_3000" ]; then
        echo "⚠️ Port 3000 still occupied by: $REMAINING_3000"
    fi
fi