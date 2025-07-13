# Local Development Setup Guide

## Option 1: Use SQLite (Easiest for Quick Start)

1. Create a `.env` file in the `backend` directory:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` and add:
   ```
   DATABASE_URL=sqlite:///development_food_app.db
   JWT_SECRET=your-local-dev-secret-key-minimum-32-chars
   # Add at least one AI API key (get from providers listed in .env.example)
   ```

3. Start the backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Option 2: Use PostgreSQL (Recommended - Matches Production)

1. Install PostgreSQL:
   - **Mac**: `brew install postgresql@15` then `brew services start postgresql@15`
   - **Ubuntu/Debian**: `sudo apt install postgresql postgresql-contrib`
   - **Windows**: Download from https://www.postgresql.org/download/windows/

2. Create the database:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE food_planning_dev;
   
   # Exit
   \q
   ```

3. Create `.env` in backend:
   ```bash
   cd backend
   cp .env.example .env
   ```

4. Edit `.env`:
   ```
   # If you set a password for postgres user, update the connection string
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/food_planning_dev
   JWT_SECRET=your-local-dev-secret-key-minimum-32-chars
   # Add AI API keys as needed
   ```

5. Start the backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Start Frontend

In a separate terminal:
```bash
cd frontend
npm install  # if not already done
npm start
```

## Verify Setup

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Troubleshooting

- **PostgreSQL connection error**: Make sure PostgreSQL is running
  - Mac: `brew services list` should show postgresql as "started"
  - Linux: `sudo systemctl status postgresql`
  
- **Port already in use**: Kill existing processes or use different ports
  
- **Missing AI API keys**: At least one AI provider key is required for meal recommendations