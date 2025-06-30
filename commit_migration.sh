#!/bin/bash
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"

echo "🚀 Committing database migration Phase 1..."

git add -A
git commit -m "Phase 1: Complete PostgreSQL migration infrastructure

✅ Configuration & Infrastructure:
- Add DATABASE_URL property to Settings with environment-based selection
- Support both SQLite (local) and PostgreSQL (production) 
- Fix Alembic configuration to use dynamic DATABASE_URL
- Import simplified models matching current SQLite schema

✅ Database Abstraction Layer:
- Create unified DatabaseService supporting both SQLite and PostgreSQL
- Add database session management with proper transaction handling
- Create SQLite session wrapper for compatibility

✅ Authentication System Migration:
- Convert auth.py to use new AuthService abstraction layer
- Migrate user registration, login, and token verification
- Maintain backward compatibility with existing API endpoints
- Add comprehensive logging and error handling

🔧 Technical Changes:
- New files: database_service.py, auth_service.py, simple_models.py
- Updated: config.py (DATABASE_URL), alembic/env.py, auth.py
- Added: test_migration.py for verification

This resolves login connection issues by providing a unified database layer
that can seamlessly switch between SQLite and PostgreSQL based on environment.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Migration Phase 1 committed successfully!"