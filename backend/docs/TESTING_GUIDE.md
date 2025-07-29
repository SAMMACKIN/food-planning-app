# Food Planning App - Testing Documentation

## Overview

The Food Planning App uses a comprehensive test suite covering backend API endpoints, service logic, and integration flows. The test framework is built on **pytest** for the backend with PostgreSQL as the test database to ensure consistency with production environments.

### Key Testing Principles
- **Production Parity**: Tests use PostgreSQL (same as production) instead of SQLite
- **Isolation**: Each test runs in isolation with proper setup/teardown
- **Coverage**: Minimum 70% code coverage threshold enforced
- **CI/CD Integration**: Automated testing on GitHub Actions for all branches

## Test Suite Structure

### Backend Tests (`/backend/tests/`)
```
tests/
├── api/                    # API endpoint tests
│   ├── test_auth_simple.py
│   ├── test_books.py
│   ├── test_family_complete.py
│   ├── test_general.py
│   ├── test_ingredients.py
│   ├── test_movies_edge_cases.py
│   ├── test_pantry_complete.py
│   └── test_recommendations.py
├── integration/            # End-to-end integration tests
│   ├── test_book_recommendations_integration.py
│   ├── test_complete_user_journey.py
│   ├── test_complete_workflow.py
│   ├── test_family_pantry_integration.py
│   └── test_recommendations_recipes.py
├── services/              # Service layer tests
│   ├── test_book_recommendation_service.py
│   ├── test_book_recommendation_service_mock.py
│   ├── test_movie_recommendation_service_advanced.py
│   └── test_shopping_list_service.py
├── security/              # Security-focused tests
│   └── test_auth_security.py
├── unit/                  # Unit tests
│   └── test_security.py
├── conftest.py           # Shared fixtures and configuration
├── test_ai_recommendations.py
├── test_movies_api.py
├── test_recipes_api.py
└── test_tv_shows_api.py
```

### Frontend Tests
- Currently being restructured
- Located in `/frontend/src/__tests__/`
- Uses Jest and React Testing Library

## Test Coverage Summary

### Current Metrics (Backend)
- **Total Tests**: 321 test functions
- **Overall Coverage**: 33.68% (target: 70%)
- **Pass Rate**: ~80% (228/285 tests passing)

### Coverage by Module
| Module | Coverage | Status |
|--------|----------|--------|
| API Endpoints | Good | ✅ Most endpoints tested |
| Services | Good | ✅ AI services well-mocked |
| Models | Partial | ⚠️ More model tests needed |
| Security | Excellent | ✅ Auth thoroughly tested |
| Integration | Good | ✅ User journeys covered |

## Running Tests

### Local Development

#### Backend Tests
```bash
# Navigate to backend directory
cd backend

# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/api/test_books.py -v

# Run tests by marker
python -m pytest -m "not slow"  # Skip slow tests
python -m pytest -m integration  # Only integration tests

# Run with specific verbosity
python -m pytest -vv  # Very verbose
python -m pytest -q   # Quiet mode

# Generate HTML coverage report
python -m pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

#### Frontend Tests (After fixes)
```bash
# Navigate to frontend directory
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage --watchAll=false

# Run specific test file
npm test -- BookRecommendations.test.tsx
```

### CI/CD Pipeline

Tests run automatically on:
- Push to `main`, `master`, or `preview` branches
- Pull requests to these branches

GitHub Actions workflow includes:
1. **Backend Tests**: PostgreSQL service, coverage reporting
2. **Frontend Tests**: Unit tests with Jest
3. **E2E Tests**: Full stack testing with Playwright
4. **Type Checking**: TypeScript and MyPy
5. **Linting**: ESLint, Flake8, Black
6. **Security Scan**: Trivy vulnerability scanner

## Key Test Scenarios

### Authentication & Security
- User registration with validation
- Login with JWT token generation
- Token verification and expiration
- Password hashing and verification
- CORS policy enforcement
- Protected endpoint access

### Content Management
- **Books**: CRUD operations, pagination, search, reading status
- **Movies**: Create, update, viewing status, favorites
- **TV Shows**: Series management, episode tracking
- **Recipes**: Save, rate, categorize, AI generation

### AI Integration
- Mock AI providers (Claude, Perplexity, Groq)
- Recommendation generation
- Feedback learning system
- Error handling for API failures

### Data Relationships
- User → Family Members → Dietary Restrictions
- User → Pantry Items → Ingredients
- User → Saved Recipes → Ratings
- User → Content Collections (Books/Movies/TV)

## Test Data Management

### Fixtures (`conftest.py`)
```python
# Key fixtures provided:
- client: TestClient instance
- test_db: PostgreSQL test database
- admin_token/admin_headers: Admin authentication
- authenticated_user/auth_headers: Regular user auth
- sample_user_data: User registration data
- mock_claude_api: AI service mocking
```

### Test Factories
```python
# Available factories:
- UserFactory: Create test users
- IngredientFactory: Create test ingredients
- FamilyMemberFactory: Create family members
```

### Predictable Test Data
```python
# Consistent test ingredient IDs
TEST_INGREDIENT_IDS = {
    'chicken_breast': 'df914ffc-6377-405e-a397-d5a0171c3e40',
    'rice': 'a420e989-5c87-42fb-85eb-2117f548845b',
    'broccoli': 'be300a0f-642d-4578-96e5-62d5afcb0f64'
}
```

## Mocking Strategies

### AI Providers
```python
# Mocked in conftest.py
@pytest.fixture
def mock_claude_api():
    with patch('ai_service.ai_service.get_meal_recommendations') as mock:
        mock.return_value = [mock_recipe_data]
        yield mock
```

### External APIs
- All external API calls are mocked
- Predictable responses for testing
- Error scenarios included

### Database
- Real PostgreSQL for authenticity
- Automatic setup/teardown
- Transaction rollback between tests

## Common Test Patterns

### API Endpoint Testing
```python
def test_create_book(client, auth_headers):
    """Standard API test pattern"""
    # Arrange
    book_data = {"title": "Test Book", "author": "Test Author"}
    
    # Act
    response = client.post("/api/v1/books", 
                          json=book_data, 
                          headers=auth_headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data["title"]
```

### Service Testing with Mocks
```python
def test_recommendation_service(mock_ai_provider):
    """Service test with external dependency mocking"""
    # Configure mock
    mock_ai_provider.return_value = expected_data
    
    # Execute service
    result = service.get_recommendations(user_context)
    
    # Verify
    assert mock_ai_provider.called_with(expected_params)
    assert result == expected_output
```

### Integration Testing
```python
@pytest.mark.integration
def test_complete_user_journey(client):
    """Full user journey test"""
    # 1. Register user
    # 2. Add family members
    # 3. Setup pantry
    # 4. Get recommendations
    # 5. Save recipes
    # Verify entire flow
```

## Troubleshooting Guide

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Ensure PostgreSQL is running
   # Check DATABASE_URL environment variable
   # For local: postgresql://postgres:password@localhost:5432/food_planning_test
   ```

2. **Import Errors**
   ```bash
   # Ensure you're in the backend directory
   # Check PYTHONPATH includes backend directory
   export PYTHONPATH=/path/to/backend:$PYTHONPATH
   ```

3. **Fixture Not Found**
   ```bash
   # Fixtures must be in conftest.py or imported
   # Check fixture scope (function/module/session)
   ```

4. **Async Test Issues**
   ```bash
   # Install pytest-asyncio
   pip install pytest-asyncio
   # Mark async tests: @pytest.mark.asyncio
   ```

5. **Test Database Not Cleaned**
   ```bash
   # Manually drop test database
   psql -U postgres -c "DROP DATABASE IF EXISTS food_planning_test"
   psql -U postgres -c "CREATE DATABASE food_planning_test"
   ```

### Debugging Tests
```bash
# Run with Python debugger
python -m pytest tests/api/test_books.py::test_create_book -s --pdb

# Show print statements
python -m pytest -s

# Show local variables on failure
python -m pytest -l

# Stop on first failure
python -m pytest -x
```

## Known Limitations

1. **Frontend Tests**: Currently need configuration fixes for module resolution
2. **Coverage Gap**: Some modules lack comprehensive tests (utils, migrations)
3. **Async Tests**: Some async endpoints not fully tested due to missing pytest-asyncio
4. **Performance**: Full test suite takes ~72 seconds (optimization needed)

## Future Improvements

### Immediate Priorities
1. Fix frontend test configuration
2. Add pytest-asyncio for async endpoint testing
3. Increase coverage to meet 70% threshold
4. Optimize slow-running tests

### Long-term Goals
1. Add mutation testing
2. Implement contract testing for API
3. Add performance benchmarking
4. Create visual regression tests for frontend
5. Implement smoke tests for production

## CI/CD Integration

### GitHub Actions Configuration
- Located in `.github/workflows/test.yml`
- Runs on every push and PR
- PostgreSQL service container
- Coverage reporting to Codecov
- Artifact upload for test results

### Environment Variables
```yaml
# Required for CI
DATABASE_URL: postgresql://test:test@localhost:5432/food_planning_test
JWT_SECRET: test-jwt-secret-for-github-actions
TESTING: "true"
# AI keys use test values (mocked)
```

### Test Markers
```ini
# pytest.ini configuration
[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests  
    api: API tests
    slow: Slow running tests
```

## Best Practices

1. **Write Tests First**: Follow TDD when possible
2. **One Assertion Per Test**: Keep tests focused
3. **Use Descriptive Names**: `test_create_book_with_invalid_isbn_returns_400`
4. **Mock External Dependencies**: Never call real APIs in tests
5. **Test Edge Cases**: Invalid input, empty data, boundaries
6. **Keep Tests Fast**: Mock slow operations
7. **Maintain Test Data**: Use factories and fixtures consistently
8. **Clean Up**: Ensure tests don't leave artifacts

## Maintenance Guidelines

### When Adding New Features
1. Write tests before implementation
2. Cover happy path and error cases
3. Add integration test if crossing boundaries
4. Update test documentation

### When Tests Fail
1. Check if it's a real failure or test issue
2. Fix the test if requirements changed
3. Update test data if schema changed
4. Document any workarounds

### Regular Maintenance
- Run full test suite before commits
- Monitor coverage trends
- Update deprecated test patterns
- Remove obsolete tests
- Keep test dependencies updated

## Commands Reference

```bash
# Quick test commands
pytest                          # Run all tests
pytest -x                       # Stop on first failure
pytest -k "book"               # Run tests matching "book"
pytest --lf                    # Run last failed tests
pytest --ff                    # Run failed tests first
pytest -v --tb=short          # Verbose with short traceback
pytest --durations=10         # Show 10 slowest tests
pytest --cov=app --cov-fail-under=70  # Enforce coverage
```

---

This testing documentation provides a comprehensive guide for understanding, running, and maintaining the Food Planning App test suite. Keep it updated as the test infrastructure evolves.