#!/bin/bash

echo "🚀 Starting Food Planning App Development Environment"
echo "=================================================="

# Change to app directory
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"

# Test migration first
echo "🧪 Testing migration..."
python3 test_migration_simple.py
if [ $? -ne 0 ]; then
    echo "❌ Migration test failed. Cannot start servers."
    exit 1
fi

# Test server startup
echo "🧪 Testing server startup..."
cd backend
python3 test_server_startup.py
if [ $? -ne 0 ]; then
    echo "❌ Server startup test failed. Cannot start servers."
    exit 1
fi
cd ..

echo "✅ All tests passed! Starting servers..."

# Kill any existing servers
echo "🛑 Stopping any existing servers..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
sleep 2

# Start backend
echo "🔧 Starting backend server..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Test backend
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8001"
    echo "📚 API Docs: http://localhost:8001/docs"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Development environment started!"
echo ""
echo "📱 Applications:"
echo "   🔧 Backend:  http://localhost:8001"
echo "   🎨 Frontend: http://localhost:3000 (starting...)"
echo "   📚 API Docs: http://localhost:8001/docs"
echo ""
echo "🛑 To stop servers:"
echo "   pkill -f uvicorn"
echo "   pkill -f 'npm start'"
echo ""
echo "💡 Test the login functionality at http://localhost:3000"