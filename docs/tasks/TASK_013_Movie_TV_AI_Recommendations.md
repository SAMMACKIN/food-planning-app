# TASK_013: Movie & TV Show AI Recommendations

## Status: PENDING

## Overview
Implement AI-powered recommendations for movies and TV shows, similar to the existing book recommendations feature. Connect the existing movie_recommendation_service.py to the frontend.

## Objectives
1. Complete the movie_recommendation_service.py implementation
2. Add recommendation API endpoints
3. Create MovieRecommendations.tsx UI (already exists, needs connection)
4. Implement feedback system for improving recommendations

## Implementation Steps

### 1. Complete Backend Service
The service already exists at `backend/app/services/movie_recommendation_service.py` but needs:
- [ ] Complete the recommendation generation logic
- [ ] Add multi-provider AI support (Claude, Perplexity, Groq)
- [ ] Implement genre-based and viewing history analysis
- [ ] Add caching for recommendations

### 2. API Endpoints
```python
# backend/app/api/movies.py - Add these endpoints
@router.post("/movies/recommendations")
async def get_movie_recommendations(
    request: MovieRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = MovieRecommendationService()
    return await service.get_recommendations(current_user.id, request, db)

@router.post("/movies/recommendations/{recommendation_id}/feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: MovieRecommendationFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Store feedback for learning
```

### 3. Frontend Integration
Update `frontend/src/pages/Movies/MovieRecommendations.tsx`:
- [ ] Connect to recommendation API endpoint
- [ ] Display AI-generated recommendations
- [ ] Add feedback buttons (Watched, Want to Watch, Not Interested)
- [ ] Show personalized reasoning for each recommendation
- [ ] Add genre/type filtering

### 4. Recommendation Prompts
```python
# Enhance prompts for better recommendations
movie_prompt = f"""
Based on the user's viewing history and preferences:
- Watched and liked: {watched_liked}
- Want to watch: {want_to_watch}
- Genres preferred: {favorite_genres}
- Average runtime preference: {avg_runtime}
- TV show vs movie preference: {content_type_preference}

Generate 5 personalized recommendations with:
1. Title and year
2. Genre and runtime
3. Why this matches their preferences
4. Similar to which watched content
5. IMDB/TMDB ID if known
"""
```

### 5. Learning System
- Track which recommendations users add to their collection
- Monitor feedback (watched, not interested)
- Adjust future recommendations based on patterns
- Store feedback in ContentRating table

## Success Criteria
- AI generates relevant movie/TV recommendations
- Users can provide feedback on recommendations
- System learns from user interactions
- Seamless integration with existing movie collection
- Fast response times with caching

## Dependencies
- Existing movie_recommendation_service.py
- AI service integration (Claude/Perplexity/Groq)
- MovieRecommendations.tsx component
- Movie collection data

## Estimated Time: 2-3 days