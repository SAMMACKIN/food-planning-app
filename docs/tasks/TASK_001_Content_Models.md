# TASK_001: Create Unified Content Models

## Overview
Create database models to support books, TV shows, and movies alongside existing recipes, using a unified content architecture that enables sharing and AI recommendations across all content types.

## Requirements
- Create base content model with common fields (title, description, user association, rating)
- Support content types: RECIPE, BOOK, TV_SHOW, MOVIE
- Maintain backward compatibility with existing recipe system
- Enable unified rating and sharing systems across all content types
- Content-specific metadata stored in JSON fields for flexibility
- User associations via foreign keys for data isolation

## Implementation Approach
- Create new database tables for books, TV shows, movies
- Add content_type enum field to support polymorphic content
- Create Pydantic schemas for new content types
- Implement database migration that preserves existing recipe data
- Update existing rating system to work with all content types
- Ensure user data isolation across all content types

## Acceptance Criteria
- [ ] All new models created and tested
- [ ] Database migration runs successfully  
- [ ] Existing recipe functionality unchanged
- [ ] New content can be created via API
- [ ] User associations work correctly
- [ ] Rating system supports all content types
- [ ] Content type validation works properly

## Testing
- [ ] Model validation tests
- [ ] Database migration tests
- [ ] API schema validation tests
- [ ] Content creation/retrieval tests
- [ ] User isolation tests
- [ ] Backward compatibility tests

## Dependencies
None - foundation task

## Estimated Time
4-6 hours