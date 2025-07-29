#!/bin/bash

echo "Running Frontend Tests..."
cd frontend
CI=true npm test -- --passWithNoTests --watchAll=false
FRONTEND_RESULT=$?

echo -e "\n\nRunning Backend Tests..."
cd ../backend
python -m pytest tests/ -v --tb=short
BACKEND_RESULT=$?

echo -e "\n\n========== TEST SUMMARY =========="
if [ $FRONTEND_RESULT -eq 0 ]; then
    echo "✅ Frontend tests: PASSED"
else
    echo "❌ Frontend tests: FAILED"
fi

if [ $BACKEND_RESULT -eq 0 ]; then
    echo "✅ Backend tests: PASSED"
else
    echo "❌ Backend tests: FAILED"
fi

exit $((FRONTEND_RESULT + BACKEND_RESULT))