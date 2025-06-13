#!/bin/bash
echo "🚀 Starting Food Planning API..."
echo "📍 Working directory: $(pwd)"
echo "🔍 Files in directory: $(ls -la)"
echo "🐍 Python version: $(python --version)"
echo "📦 Installed packages: $(pip list | head -20)"
echo "🔧 Environment variables:"
echo "  PORT: $PORT"
echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "  JWT_SECRET_KEY: ${JWT_SECRET_KEY:+SET}"
echo "  DATABASE_URL: $DATABASE_URL"

# Start the application
python -m uvicorn simple_app:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info