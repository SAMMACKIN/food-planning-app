#!/bin/bash
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app/backend"
echo "Starting FastAPI backend with PostgreSQL..."
echo "Working directory: $(pwd)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload