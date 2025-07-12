# Health App/Food Planning App - Complete Codebase Structure Analysis

## Overview
This document provides a comprehensive analysis of every single file in the Health App/Food Planning App codebase, including descriptions, purposes, git status, and deletion recommendations.

---

## ROOT LEVEL FILES

### System Files
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.DS_Store` | macOS System | N/A | macOS Finder metadata | System metadata for folder view preferences | ❌ No | ✅ Yes - Now |

### Claude Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.claude/settings.local.json` | JSON Config | ~20 | Claude Code local settings | Stores user preferences for Claude Code tool | ❌ No | ❌ No - User settings |

---

## FOOD-PLANNING-APP DIRECTORY

### Root Configuration & Documentation
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `README.md` | Markdown | 93 | Project overview and setup instructions | Main project documentation | ✅ Yes | ❌ No |
| `CLAUDE.md` | Markdown | 156 | Development guide for AI assistants | AI assistant context and guidelines | ✅ Yes | ❌ No |
| `TODO.md` | Markdown | 234 | Project task tracking | Development roadmap and pending tasks | ✅ Yes | ❌ No |
| `DEPLOYMENT.md` | Markdown | 178 | Deployment instructions | Production deployment guide | ✅ Yes | ❌ No |
| `DEPLOYMENT_COMMANDS.md` | Markdown | ~50 | Quick deployment commands | Command reference for deployments | ✅ Yes | ❌ No |
| `DEPLOY_TO_PREVIEW_NOW.md` | Markdown | ~30 | Preview deployment guide | Staging environment deployment | ✅ Yes | ❌ No |
| `PREVIEW_WORKFLOW.md` | Markdown | ~40 | Preview workflow documentation | Development workflow for staging | ✅ Yes | ❌ No |
| `DATABASE_FIXES_SUMMARY.md` | Markdown | ~60 | Database migration notes | Documents database schema changes | ✅ Yes | ❌ No |
| `DEBUG_RECIPE_SAVING.md` | Markdown | 89 | Recipe debugging guide | Troubleshooting guide for recipe features | ✅ Yes | ❌ No |
| `REFACTORING_PLAN.md` | Markdown | ~100 | Code refactoring roadmap | Plans for code improvements | ✅ Yes | ❌ No |

### Environment & Git Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.env` | Environment | ~10 | Local environment variables | Development environment configuration | ❌ No | ❌ No - Contains secrets |
| `.env.example` | Environment | ~10 | Example environment variables | Template for environment setup | ✅ Yes | ❌ No |
| `.gitignore` | Git Config | ~30 | Git ignore rules | Specifies files to exclude from git | ✅ Yes | ❌ No |
| `.vercelignore` | Vercel Config | ~10 | Vercel deployment ignore rules | Files to exclude from Vercel builds | ✅ Yes | ❌ No |

### Deployment Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `Procfile` | Heroku Config | 1 | Heroku process definition | Defines how Heroku runs the app | ✅ Yes | ❌ No |
| `vercel.json` | JSON Config | 34 | Vercel deployment configuration | Frontend deployment settings for Vercel | ✅ Yes | ❌ No |
| `railway.json` | JSON Config | 23 | Railway deployment configuration | Backend deployment settings for Railway | ✅ Yes | ❌ No |
| `docker-compose.yml` | YAML Config | 68 | Multi-container Docker setup | Local development with Docker | ✅ Yes | ❌ No |

### CI/CD
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.github/workflows/test.yml` | YAML Config | ~50 | GitHub Actions CI/CD pipeline | Automated testing on push/PR | ✅ Yes | ❌ No |

### Test Scripts
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `RECIPE_SAVING_TEST.js` | JavaScript | ~100 | Recipe functionality test script | Manual testing script for recipes | ✅ Yes | ⚠️ Maybe - If automated tests cover this |
| `test_recipe_saving.js` | JavaScript | ~80 | Another recipe test script | Duplicate/legacy test script | ✅ Yes | ✅ Yes - Likely redundant |

### System Files
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.DS_Store` | macOS System | N/A | macOS Finder metadata | System metadata | ❌ No | ✅ Yes - Now |

---

## GIT DIRECTORY (.git/)

### Core Git Files
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.git/HEAD` | Git Internal | 1 | Current branch pointer | Points to current branch | N/A | ❌ No - Git needs this |
| `.git/config` | Git Config | ~20 | Repository configuration | Git settings and remotes | N/A | ❌ No - Git needs this |
| `.git/description` | Git Internal | 1 | Repository description | Used by GitWeb (rarely used) | N/A | ❌ No - Git standard |
| `.git/index` | Git Internal | Binary | Staging area | Git staging index | N/A | ❌ No - Git needs this |
| `.git/COMMIT_EDITMSG` | Git Internal | ~5 | Last commit message | Template for commit messages | N/A | ❌ No - Git needs this |
| `.git/FETCH_HEAD` | Git Internal | ~5 | Last fetch information | Records last fetch operation | N/A | ❌ No - Git needs this |
| `.git/ORIG_HEAD` | Git Internal | 1 | Original HEAD before operations | Backup of HEAD before merge/rebase | N/A | ❌ No - Git needs this |

### Git Hooks (All Sample Files)
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.git/hooks/*.sample` | Shell Scripts | Various | Git hook examples | Template scripts for git events | N/A | ✅ Yes - Sample files only |

### Git Refs & Logs
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.git/refs/heads/*` | Git Internal | 1 each | Branch references | Points to commit hashes for branches | N/A | ❌ No - Git needs this |
| `.git/refs/remotes/*` | Git Internal | 1 each | Remote branch references | Points to remote branch commits | N/A | ❌ No - Git needs this |
| `.git/refs/stash` | Git Internal | 1 | Stash reference | Points to stashed changes | N/A | ⚠️ Only if no stashes needed |
| `.git/logs/*` | Git Internal | Various | Git operation logs | History of git operations | N/A | ❌ No - Git needs this |

### Git Objects
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.git/objects/*/*` | Git Internal | Binary | Git object database | Stores all commits, trees, blobs | N/A | ❌ No - Git needs this |

---

## BACKEND DIRECTORY

### Core Application Files
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/main.py` | Python | 99 | FastAPI application entry point | Creates and configures the FastAPI app | ✅ Yes | ❌ No |
| `backend/simple_app.py` | Python | 2,366 | Legacy monolithic application | **LEGACY** - Single-file app, replaced by modular app/ | ✅ Yes | ⚠️ Yes - After confirming no dependencies |

### Core Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/core/config.py` | Python | 173 | Application configuration | Settings, environment variables, database URLs | ✅ Yes | ❌ No |
| `backend/app/core/database_service.py` | Python | 210 | **CURRENT** Database service | Modern PostgreSQL/SQLite database layer | ✅ Yes | ❌ No |
| `backend/app/core/auth_service.py` | Python | 144 | Authentication service | Modern auth service with JWT handling | ✅ Yes | ❌ No |
| `backend/app/core/security.py` | Python | 32 | Security utilities | JWT token handling, password hashing | ✅ Yes | ❌ No |
| ~~`backend/app/core/database_legacy.py.bak`~~ | ~~Python~~ | ~~227~~ | ~~Legacy database code~~ | ~~Removed - backup file~~ | ❌ DELETED | ✅ DELETED |

### API Endpoints
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/api/auth.py` | Python | 253 | Authentication endpoints | Login, register, token refresh (5 routes) | ✅ Yes | ❌ No |
| `backend/app/api/recipes.py` | Python | 749 | Recipe management endpoints | CRUD operations for recipes (8 routes) | ✅ Yes | ❌ No |
| `backend/app/api/recommendations.py` | Python | 382 | AI recommendation endpoints | Claude AI meal recommendations (3 routes) | ✅ Yes | ❌ No |
| `backend/app/api/meal_plans.py` | Python | 435 | Meal planning endpoints | Weekly meal planning (6 routes) | ✅ Yes | ❌ No |
| `backend/app/api/pantry.py` | Python | 410 | Pantry management endpoints | Inventory tracking (7 routes) | ✅ Yes | ❌ No |
| `backend/app/api/family.py` | Python | 306 | Family member endpoints | Family management (5 routes) | ✅ Yes | ❌ No |
| `backend/app/api/admin.py` | Python | 339 | Admin dashboard endpoints | Admin functionality (6 routes) | ✅ Yes | ❌ No |

### API Routing
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/api/api_v1/api.py` | Python | ~50 | API v1 router | Groups all v1 endpoints | ✅ Yes | ❌ No |
| `backend/app/api/endpoints/auth.py` | Python | ~100 | **DUPLICATE** auth endpoints | Duplicate of api/auth.py | ✅ Yes | ✅ Yes - Duplicate |

### Database Models
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/models/user.py` | Python | 26 | User SQLAlchemy model | User database schema | ✅ Yes | ❌ No |
| `backend/app/models/family.py` | Python | 39 | Family member model | Family member database schema | ✅ Yes | ❌ No |
| `backend/app/models/ingredient.py` | Python | 71 | Ingredient models | Ingredient and category database schemas | ✅ Yes | ❌ No |
| `backend/app/models/meal.py` | Python | 58 | Meal-related models | Recipe, meal, meal plan schemas (4 classes) | ✅ Yes | ❌ No |
| `backend/app/models/planning.py` | Python | 45 | Planning models | Meal planning related schemas | ✅ Yes | ❌ No |
| `backend/app/models/preferences.py` | Python | 32 | User preferences model | User dietary preferences schema | ✅ Yes | ❌ No |
| `backend/app/models/recipe.py` | Python | 57 | Recipe model | Legacy recipe database schema | ✅ Yes | ❌ No |
| `backend/app/models/recipe_v2.py` | Python | 47 | **CURRENT** RecipeV2 model | Modern recipe database schema | ✅ Yes | ❌ No |
| ~~`backend/app/models/simple_models.py.backup`~~ | ~~Python~~ | ~~166~~ | ~~Legacy models backup~~ | ~~Removed - backup file~~ | ❌ DELETED | ✅ DELETED |

### Pydantic Schemas (API Validation)
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/app/schemas/auth.py` | Python | 67 | Authentication schemas | Request/response validation for auth | ✅ Yes | ❌ No |
| `backend/app/schemas/meals.py` | Python | 159 | Meal schemas | Request/response validation for meals | ✅ Yes | ❌ No |
| `backend/app/schemas/family.py` | Python | 42 | Family schemas | Request/response validation for family | ✅ Yes | ❌ No |
| `backend/app/schemas/pantry.py` | Python | 38 | Pantry schemas | Request/response validation for pantry | ✅ Yes | ❌ No |
| `backend/app/schemas/user.py` | Python | 29 | User schemas | Request/response validation for users | ✅ Yes | ❌ No |
| `backend/app/schemas/recipe_v2.py` | Python | 117 | **CURRENT** RecipeV2 schemas | Modern recipe validation schemas | ✅ Yes | ❌ No |

### AI Services
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/ai_service.py` | Python | 391 | **CURRENT** Claude AI integration | Modern AI service for recommendations | ✅ Yes | ❌ No |
| `backend/claude_service.py` | Python | 249 | **LEGACY** Claude service | Legacy AI service implementation | ✅ Yes | ⚠️ Yes - Replaced by ai_service.py |

### Database Management
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/alembic.ini` | Config | 94 | **Alembic configuration** | Database migration tool settings | ✅ Yes | ❌ No |
| `backend/alembic/env.py` | Python | 91 | **Alembic environment** | Migration environment setup | ✅ Yes | ❌ No |
| `backend/alembic/script.py.mako` | Template | ~30 | **Alembic migration template** | Template for new migrations | ✅ Yes | ❌ No |
| `backend/migrate_meal_plans.py` | Python | 78 | Custom migration script | Specific data migration for meal plans | ✅ Yes | ⚠️ Maybe - After migration complete |
| ~~`backend/debug_database.py`~~ | ~~Python~~ | ~~45~~ | ~~Database debugging utility~~ | ~~Removed - obsolete with PostgreSQL~~ | ❌ DELETED | ✅ DELETED |
| ~~`backend/migrate_recipes_v2.py`~~ | ~~Python~~ | ~~125~~ | ~~RecipeV2 migration script~~ | ~~Removed - migration completed~~ | ❌ DELETED | ✅ DELETED |
| ~~`backend/ensure_recipes_v2.py`~~ | ~~Python~~ | ~~126~~ | ~~Recipe table validation~~ | ~~Removed - handled in startup~~ | ❌ DELETED | ✅ DELETED |

> **What is Alembic?** Alembic is a database migration tool for SQLAlchemy. It manages database schema changes over time, allowing you to version control your database structure and apply changes incrementally in different environments.

### Database Files (Development)
| File | Type | Size | Description | Purpose | Git Status | Can Delete |
|------|------|------|-------------|---------|------------|------------|
| `backend/development_food_app.db` | SQLite | ~1MB | Development database | Local development data | ❌ No | ✅ Yes - Regenerated |
| `backend/food_planning.db` | SQLite | ~2MB | Main development database | Primary local database | ❌ No | ✅ Yes - Regenerated |
| `backend/simple_food_app.db` | SQLite | ~500KB | Legacy database | Database for simple_app.py | ❌ No | ✅ Yes - Legacy |

### Log Files
| File | Type | Size | Description | Purpose | Git Status | Can Delete |
|------|------|------|-------------|---------|------------|------------|
| `backend/backend.log` | Log | ~10KB | Backend application logs | Runtime logs and errors | ❌ No | ✅ Yes - Regenerated |
| `backend/server.log` | Log | ~5KB | Server logs | Web server logs | ❌ No | ✅ Yes - Regenerated |
| `backend/simple_backend.log` | Log | ~3KB | Legacy app logs | Logs from simple_app.py | ❌ No | ✅ Yes - Legacy |

### Environment & Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `.env` | Environment | ~15 | Local environment variables | Database URLs, API keys, secrets | ❌ No | ❌ No - Contains secrets |
| `.env.example` | Environment | ~15 | Example environment variables | Template for environment setup | ✅ Yes | ❌ No |
| `requirements.txt` | Text | 25 | Python dependencies | pip package requirements | ✅ Yes | ❌ No |
| `pytest.ini` | Config | 12 | **Pytest configuration** | Python test runner settings | ✅ Yes | ❌ No |
| `Dockerfile` | Docker Config | ~30 | Docker container definition | Backend containerization | ✅ Yes | ❌ No |
| `nixpacks.toml` | Config | 8 | Nixpacks deployment config | Railway deployment settings | ✅ Yes | ❌ No |

### Development & Debug Scripts (REMOVED)
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| ~~`test_config_simple.py`~~ | ~~Python~~ | ~~47~~ | ~~Config testing script~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |
| ~~`test_db_connection.py`~~ | ~~Python~~ | ~~76~~ | ~~Database connection test~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |
| ~~`test_migration.py`~~ | ~~Python~~ | ~~82~~ | ~~Migration testing script~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |
| ~~`test_server_startup.py`~~ | ~~Python~~ | ~~48~~ | ~~Server startup test~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |
| ~~`test_startup_fixed.py`~~ | ~~Python~~ | ~~177~~ | ~~Startup fix test~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |
| ~~`run_startup_test.py`~~ | ~~Python~~ | ~~13~~ | ~~Startup test runner~~ | ~~Removed - development tool~~ | ❌ DELETED | ✅ DELETED |

### Python Cache & Virtual Environment
| File/Directory | Type | Size | Description | Purpose | Git Status | Can Delete |
|----------------|------|------|-------------|---------|------------|------------|
| `__pycache__/` | Python Cache | Various | **Python bytecode cache** | Compiled Python files for faster loading | ❌ No | ✅ Yes - Regenerated |
| `venv/` | Virtual Environment | ~500MB | **Python virtual environment** | Isolated Python environment with dependencies | ❌ No | ✅ Yes - Recreatable |

> **What is venv?** Virtual environment (venv) is an isolated Python environment that contains its own Python interpreter and packages. It prevents conflicts between different projects' dependencies.

### Test Cache
| File/Directory | Type | Size | Description | Purpose | Git Status | Can Delete |
|----------------|------|------|-------------|---------|------------|------------|
| `.pytest_cache/` | Test Cache | ~1MB | **Pytest cache directory** | Cached test results and metadata | ❌ No | ✅ Yes - Regenerated |

---

## BACKEND TESTS

### Test Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/conftest.py` | Python | 78 | **Pytest configuration** | Test fixtures and setup | ✅ Yes | ❌ No |
| `backend/tests/test_runner.py` | Python | ~30 | Test runner utility | Helper for running tests | ✅ Yes | ❌ No |

### API Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/api/test_auth_simple.py` | Python | 89 | Authentication API tests | Tests login, register, token refresh | ✅ Yes | ❌ No |
| `backend/tests/api/test_family_complete.py` | Python | 156 | Family API tests | Tests family member management | ✅ Yes | ❌ No |
| `backend/tests/api/test_pantry_complete.py` | Python | 187 | Pantry API tests | Tests inventory management | ✅ Yes | ❌ No |
| `backend/tests/api/test_recommendations.py` | Python | 98 | AI recommendations tests | Tests Claude AI integration | ✅ Yes | ❌ No |
| `backend/tests/api/test_ingredients.py` | Python | 134 | Ingredients API tests | Tests ingredient management | ✅ Yes | ❌ No |
| `backend/tests/api/test_general.py` | Python | ~50 | General API tests | Tests health checks, basic endpoints | ✅ Yes | ❌ No |

### Integration Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/integration/test_complete_user_journey.py` | Python | 462 | **End-to-end user flow tests** | Tests complete user workflows | ✅ Yes | ❌ No |

### Security Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/security/test_auth_security.py` | Python | 89 | Security tests | Tests authentication security | ✅ Yes | ❌ No |

### Unit Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/unit/test_security.py` | Python | ~40 | Security unit tests | Tests security utility functions | ✅ Yes | ❌ No |

### AI Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `backend/tests/test_ai_recommendations.py` | Python | 67 | AI service tests | Tests Claude AI integration | ✅ Yes | ❌ No |

---

## FRONTEND DIRECTORY

### Core Application
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/App.tsx` | TypeScript/React | 110 | **Main React application** | Root component with routing | ✅ Yes | ❌ No |
| `frontend/src/index.tsx` | TypeScript | 19 | **React application entry point** | Bootstraps React app | ✅ Yes | ❌ No |
| `frontend/src/react-app-env.d.ts` | TypeScript | 1 | **React TypeScript definitions** | Type definitions for React | ✅ Yes | ❌ No |
| `frontend/src/reportWebVitals.ts` | TypeScript | ~20 | **Web performance monitoring** | Measures app performance | ✅ Yes | ⚠️ Maybe - If not monitoring |
| `frontend/src/setupTests.ts` | TypeScript | ~5 | **Jest test setup** | Test environment configuration | ✅ Yes | ❌ No |

### Services & API
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/services/api.ts` | TypeScript | 72 | **API client** | HTTP client with auth interceptors | ✅ Yes | ❌ No |

### State Management
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/store/authStore.ts` | TypeScript | 129 | **Zustand auth store** | Global authentication state | ✅ Yes | ❌ No |

### Type Definitions
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/types/index.ts` | TypeScript | 289 | **TypeScript type definitions** | All app type definitions | ✅ Yes | ❌ No |

### Custom Hooks
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/hooks/useRecipes.ts` | TypeScript | 268 | **Recipe management hook** | Recipe CRUD operations | ✅ Yes | ❌ No |
| `frontend/src/hooks/useRecommendationsCache.ts` | TypeScript | 134 | **Recommendations caching hook** | Caches AI recommendations | ✅ Yes | ❌ No |

### Context Providers
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/contexts/ThemeContext.tsx` | React | 67 | **Theme context provider** | Global theme state management | ✅ Yes | ❌ No |

### Theme & Styling
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/theme/index.ts` | TypeScript | 819 | **Material-UI theme configuration** | Custom theme, colors, typography | ✅ Yes | ❌ No |
| `frontend/src/App.css` | CSS | ~50 | **Application styles** | Global CSS styles | ✅ Yes | ❌ No |
| `frontend/src/index.css` | CSS | ~30 | **Root styles** | Base HTML/body styles | ✅ Yes | ❌ No |

---

## FRONTEND PAGES

### Authentication Pages
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/pages/Auth/Login.tsx` | React | 110 | **Login page** | User authentication form | ✅ Yes | ❌ No |
| `frontend/src/pages/Auth/Register.tsx` | React | 124 | **Registration page** | User signup form | ✅ Yes | ❌ No |

### Main Application Pages
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/pages/Dashboard/Dashboard.tsx` | React | 276 | **Main dashboard** | App home page with overview | ✅ Yes | ❌ No |
| `frontend/src/pages/Recommendations/MealRecommendations.tsx` | React | 842 | **AI recommendations page** | Claude AI meal suggestions | ✅ Yes | ❌ No |
| `frontend/src/pages/MealPlanning/MealPlanning.tsx` | React | 570 | **Meal planning page** | Weekly meal planning interface | ✅ Yes | ❌ No |
| `frontend/src/pages/Pantry/PantryManagement.tsx` | React | 520 | **Pantry management page** | Inventory tracking interface | ✅ Yes | ❌ No |
| `frontend/src/pages/Family/FamilyManagement.tsx` | React | 407 | **Family management page** | Family member management | ✅ Yes | ❌ No |
| `frontend/src/pages/Admin/AdminDashboard.tsx` | React | 665 | **Admin dashboard** | Administrative interface | ✅ Yes | ❌ No |

### Information Pages
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/pages/UserGuide/UserGuide.tsx` | React | 298 | **User guide page** | Help and documentation | ✅ Yes | ❌ No |
| `frontend/src/pages/Changes/Changes.tsx` | React | 156 | **Changelog page** | App updates and changes | ✅ Yes | ❌ No |

---

## FRONTEND COMPONENTS

### Layout Components
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/components/Layout/Layout.tsx` | React | 572 | **Main app layout** | Navigation, sidebar, header | ✅ Yes | ❌ No |

### UI Components
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/components/Loading/LoadingSpinner.tsx` | React | 45 | **Loading spinner component** | Loading state indicator | ✅ Yes | ❌ No |
| `frontend/src/components/ThemeToggle.tsx` | React | 78 | **Theme toggle component** | Dark/light mode switcher | ✅ Yes | ❌ No |

### Recipe Components
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/components/Recipe/CreateRecipeForm.tsx` | React | 234 | **Recipe creation form** | Form for adding new recipes | ✅ Yes | ❌ No |
| `frontend/src/components/Recipe/RecipeInstructions.tsx` | React | 187 | **Recipe instructions display** | Shows recipe steps | ✅ Yes | ❌ No |
| `frontend/src/components/Recipe/RecipeDebugPanel.tsx` | React | 89 | **Recipe debugging panel** | Development tool for recipe issues | ✅ Yes | ⚠️ Maybe - Development tool |

---

## FRONTEND TESTS

### Component Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/components/__tests__/LoadingSpinner.test.tsx` | TypeScript/Jest | 34 | Loading spinner tests | Unit tests for loading component | ✅ Yes | ❌ No |

### Service Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/services/__tests__/api.test.ts` | TypeScript/Jest | 67 | API service tests | Tests API client functionality | ✅ Yes | ❌ No |

### Store Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/store/__tests__/authStore.test.ts` | TypeScript/Jest | 89 | Auth store tests | Tests authentication state | ✅ Yes | ❌ No |

### Type Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/types/__tests__/index.test.ts` | TypeScript/Jest | 45 | Type definition tests | Tests TypeScript types | ✅ Yes | ❌ No |

### E2E Tests
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/e2e/auth.spec.ts` | TypeScript/Playwright | ~100 | **End-to-end auth tests** | Full browser testing for auth | ✅ Yes | ❌ No |
| `frontend/e2e/navigation.spec.ts` | TypeScript/Playwright | ~80 | **End-to-end navigation tests** | Full browser testing for navigation | ✅ Yes | ❌ No |

---

## FRONTEND CONFIGURATION

### Package Management
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/package.json` | JSON | 95 | **NPM package configuration** | Dependencies, scripts, metadata | ✅ Yes | ❌ No |
| `frontend/package-lock.json` | JSON | ~50,000 | **NPM dependency lock file** | Exact dependency versions | ✅ Yes | ❌ No |

### TypeScript Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/tsconfig.json` | JSON | 25 | **TypeScript configuration** | TypeScript compiler settings | ✅ Yes | ❌ No |

### Testing Configuration
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/playwright.config.ts` | TypeScript | 78 | **Playwright E2E test config** | End-to-end testing configuration | ✅ Yes | ❌ No |

### Environment Files
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/.env.local` | Environment | ~5 | Local development environment | Development-specific variables | ❌ No | ❌ No - Local config |
| `frontend/.env.production` | Environment | ~5 | Production environment | Production-specific variables | ❌ No | ❌ No - Prod config |
| `frontend/.env.preview` | Environment | ~5 | Preview environment | Staging-specific variables | ❌ No | ❌ No - Staging config |

### Build & Deployment
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/Dockerfile` | Docker Config | ~25 | Frontend Docker container | Production containerization | ✅ Yes | ❌ No |
| `frontend/nginx.conf` | Nginx Config | ~30 | Web server configuration | Production web server setup | ✅ Yes | ❌ No |
| `frontend/build-for-branch.sh` | Shell Script | ~20 | Branch-specific build script | Automated building for different branches | ✅ Yes | ❌ No |

### Public Assets
| File | Type | Size | Description | Purpose | Git Status | Can Delete |
|------|------|------|-------------|---------|------------|------------|
| `frontend/public/index.html` | HTML | ~50 lines | **React app HTML template** | Base HTML file for React | ✅ Yes | ❌ No |
| `frontend/public/favicon.ico` | Icon | ~4KB | **App favicon** | Browser tab icon | ✅ Yes | ❌ No |
| `frontend/public/logo192.png` | Image | ~5KB | **App logo (192px)** | PWA logo | ✅ Yes | ❌ No |
| `frontend/public/logo512.png` | Image | ~9KB | **App logo (512px)** | PWA logo | ✅ Yes | ❌ No |
| `frontend/public/manifest.json` | JSON | ~20 lines | **PWA manifest** | Progressive Web App configuration | ✅ Yes | ❌ No |
| `frontend/public/robots.txt` | Text | ~5 lines | **Search engine instructions** | SEO crawler instructions | ✅ Yes | ❌ No |

### Development Artifacts
| File/Directory | Type | Size | Description | Purpose | Git Status | Can Delete |
|----------------|------|------|-------------|---------|------------|------------|
| `frontend/node_modules/` | Dependencies | ~2GB | **NPM dependencies** | Installed packages | ❌ No | ✅ Yes - Reinstallable |
| `frontend/build/` | Build Output | ~10MB | **Production build output** | Compiled React app | ❌ No | ✅ Yes - Regenerated |
| `frontend/coverage/` | Test Coverage | ~5MB | **Test coverage reports** | Code coverage HTML reports | ❌ No | ✅ Yes - Regenerated |

### Log Files
| File | Type | Size | Description | Purpose | Git Status | Can Delete |
|------|------|------|-------------|---------|------------|------------|
| `frontend/frontend.log` | Log | ~8KB | Frontend development logs | Runtime logs and errors | ❌ No | ✅ Yes - Regenerated |
| `frontend/server.log` | Log | ~3KB | Development server logs | Webpack dev server logs | ❌ No | ✅ Yes - Regenerated |

### Mock Data
| File | Type | Lines | Description | Purpose | Git Status | Can Delete |
|------|------|-------|-------------|---------|------------|------------|
| `frontend/src/__mocks__/` | Directory | Various | **Mock data for testing** | Test fixtures and mock responses | ✅ Yes | ❌ No |

### Utility Directories
| File/Directory | Type | Description | Purpose | Git Status | Can Delete |
|----------------|------|-------------|---------|------------|------------|
| `frontend/src/utils/` | Directory | **Utility functions** | Helper functions and utilities | ✅ Yes | ❌ No |

---

## SUMMARY OF DELETION RECOMMENDATIONS

### 🔴 DELETE IMMEDIATELY (Free up ~3GB+ space)
| Category | Files | Reason |
|----------|-------|---------|
| **Virtual Environment** | `backend/venv/` | Reinstallable with `python -m venv venv` |
| **Node Modules** | `frontend/node_modules/` | Reinstallable with `npm install` |
| **Build Artifacts** | `frontend/build/`, `frontend/coverage/` | Regenerated with `npm run build`, `npm test` |
| **Cache Files** | All `__pycache__/`, `.pytest_cache/` | Regenerated automatically |
| **Log Files** | `*.log` files | Regenerated during development |
| **Database Files** | `*.db` files | Recreated with migrations |
| **System Files** | `.DS_Store` | macOS system files |

### ⚠️ CONSIDER DELETING LATER (After verification)
| File | Reason | Verification Needed |
|------|--------|-------------------|
| `backend/simple_app.py` | Legacy monolithic app | Confirm no production dependencies |
| `backend/claude_service.py` | Legacy AI service | Confirm ai_service.py covers all functionality |
| `backend/app/models/simple_user.py` | Legacy user model | Confirm not used by simple_app.py |
| `backend/app/api/endpoints/auth.py` | Duplicate auth endpoints | Confirm api/auth.py is complete |
| `test_recipe_saving.js` | Potential duplicate test | Check if automated tests cover this |
| `backend/migrate_meal_plans.py` | Migration script | After migration is complete |
| Recipe debug components | Development tools | In production builds |

### ✅ KEEP - ESSENTIAL FILES
- All source code in `backend/app/` and `frontend/src/`
- All configuration files (`package.json`, `requirements.txt`, etc.)
- All documentation (`*.md` files)
- All test files
- Git configuration (`.git/` directory)
- Environment templates (`.env.example`)

### 🚫 NEVER DELETE
- `.env` files (contain secrets)
- Git directory (`.git/`)
- Package configuration files
- Source code files
- Test files
- Documentation

---

## DISK SPACE ANALYSIS

**Current Total Size:** ~3.5GB  
**After Cleanup:** ~500MB  
**Space Saved:** ~3GB (85% reduction)

**Largest Directories:**
1. `frontend/node_modules/` - ~2GB
2. `backend/venv/` - ~500MB
3. `frontend/build/` - ~10MB
4. `.git/` - ~50MB
5. Source code - ~100MB

This analysis shows a healthy, well-structured full-stack application with modern best practices, comprehensive testing, and proper deployment configurations. The main opportunities for cleanup are removing regeneratable development artifacts.