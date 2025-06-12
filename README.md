# Food Planning App

A comprehensive meal planning application that provides intelligent meal recommendations based on family preferences, dietary restrictions, available ingredients, and attendance patterns.

## Architecture

- **Backend**: FastAPI with Python 3.11+, PostgreSQL, Redis
- **Frontend**: React 18+ with TypeScript
- **AI Integration**: Claude API for meal recommendations

## Project Structure

```
food-planning-app/
├── backend/          # FastAPI backend application
├── frontend/         # React frontend application
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis
- Docker (optional)

### Development Setup

1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

3. **Environment Variables**:
   - Copy `.env.example` to `.env` in both backend and frontend directories
   - Configure database connections and API keys

4. **Database Setup**:
   ```bash
   # From backend directory
   alembic upgrade head
   python scripts/seed_data.py
   ```

5. **Running the Application**:
   ```bash
   # Backend (from backend directory)
   uvicorn app.main:app --reload

   # Frontend (from frontend directory)
   npm run dev
   ```

## Features

- **Family Member Management**: Add family members with dietary preferences and restrictions
- **Meal Recommendations**: AI-powered meal suggestions based on preferences and available ingredients
- **Pantry Management**: Track ingredients with quantities and expiration dates
- **Weekly Meal Planning**: Plan meals with attendance tracking and portion calculation
- **Ingredient Optimization**: Minimize waste and maximize ingredient reuse
- **Specialized Diet Support**: Support for keto, medical dietary requirements, and more
- **Learning System**: Improves recommendations based on user feedback

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.