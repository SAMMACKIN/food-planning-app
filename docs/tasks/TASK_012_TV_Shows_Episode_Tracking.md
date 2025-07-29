# TASK_012: TV Shows Episode Tracking

## Status: IN PROGRESS

## Overview
Enhance the existing TV & Movies page to support full TV show tracking with episode management, season progress, and viewing history.

## Objectives
1. Extend backend models to support TV show episodes and seasons
2. Update MoviesManagement.tsx to handle both movies and TV shows
3. Implement episode tracking UI with season/episode progress
4. Add viewing progress indicators and completion tracking

## Implementation Steps

### 1. Backend Model Extensions
- [ ] Add TVShow specific fields to Movie model or create separate model
- [ ] Create Episode model with season/episode numbers
- [ ] Add viewing progress tracking for episodes
- [ ] Create API endpoints for episode management

### 2. Backend API Updates
```python
# backend/app/api/movies.py - Add TV show specific endpoints
@router.get("/movies/{movie_id}/episodes")
@router.post("/movies/{movie_id}/episodes/{episode_id}/watched")
@router.get("/movies/{movie_id}/progress")
```

### 3. Frontend Updates
- [ ] Modify MoviesManagement.tsx to detect and handle TV shows
- [ ] Add episode grid/list view for TV shows
- [ ] Implement season selector and episode cards
- [ ] Add progress bars for season/series completion
- [ ] Create episode marking UI (watched/unwatched)

### 4. Database Schema
```sql
-- Add to content table or create new
ALTER TABLE movies ADD COLUMN total_seasons INTEGER;
ALTER TABLE movies ADD COLUMN total_episodes INTEGER;
ALTER TABLE movies ADD COLUMN episode_runtime INTEGER;

-- New episodes table
CREATE TABLE episodes (
    id UUID PRIMARY KEY,
    movie_id UUID REFERENCES movies(id),
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    title VARCHAR(255),
    air_date DATE,
    watched BOOLEAN DEFAULT FALSE,
    watched_date TIMESTAMP
);
```

### 5. UI Components
- SeasonSelector component
- EpisodeCard component  
- SeriesProgressBar component
- EpisodeCheckbox for marking watched

## Success Criteria
- Users can track TV shows with episode-level granularity
- Season and series progress is visually displayed
- Seamless integration with existing movie tracking
- Mobile-responsive episode management

## Dependencies
- Existing Movies infrastructure
- Movie model and API endpoints
- MoviesManagement.tsx component

## Estimated Time: 3-4 days