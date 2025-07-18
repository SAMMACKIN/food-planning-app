"""
Movie and TV Show Recommendation Service
"""
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..models.content import Movie, ContentRating
from ..schemas.movies import ViewingStatus

logger = logging.getLogger(__name__)


class MovieRecommendationService:
    """Service for generating AI-powered movie and TV show recommendations"""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
    def get_user_viewing_context(self, user_id: str, db: Session, content_type: Optional[str] = None) -> Dict[str, Any]:
        """Get user's viewing history and preferences for recommendation context"""
        
        # Get user's movies/shows with ratings
        query = db.query(Movie).filter(Movie.user_id == user_id)
        
        # Filter by content type if specified
        if content_type == 'movie':
            query = query.filter(~Movie.genre.contains('TV Series'))
        elif content_type == 'tv':
            query = query.filter(Movie.genre.contains('TV Series'))
            
        all_content = query.all()
        
        # Get ratings
        ratings = db.query(ContentRating).filter(
            ContentRating.user_id == user_id,
            ContentRating.movie_id.isnot(None)
        ).all()
        
        rating_lookup = {str(rating.movie_id): rating.rating for rating in ratings}
        
        # Categorize content
        watched = []
        want_to_watch = []
        highly_rated = []
        poorly_rated = []
        favorite_genres = {}
        favorite_directors = {}
        
        for item in all_content:
            item_dict = {
                'title': item.title,
                'genre': item.genre,
                'director': item.director,
                'year': item.release_year,
                'is_favorite': item.is_favorite,
                'rating': rating_lookup.get(str(item.id))
            }
            
            if item.viewing_status == ViewingStatus.WATCHED:
                watched.append(item_dict)
                
                # Track ratings
                if item_dict['rating']:
                    if item_dict['rating'] >= 4:
                        highly_rated.append(item_dict)
                    elif item_dict['rating'] <= 2:
                        poorly_rated.append(item_dict)
                
                # Track genres
                if item.genre:
                    genres = [g.strip() for g in item.genre.split(',')]
                    for genre in genres:
                        favorite_genres[genre] = favorite_genres.get(genre, 0) + 1
                        if item_dict['rating'] and item_dict['rating'] >= 4:
                            favorite_genres[genre] += 2  # Bonus for highly rated
                            
                # Track directors
                if item.director:
                    favorite_directors[item.director] = favorite_directors.get(item.director, 0) + 1
                    if item_dict['rating'] and item_dict['rating'] >= 4:
                        favorite_directors[item.director] += 2
                        
            elif item.viewing_status == ViewingStatus.WANT_TO_WATCH:
                want_to_watch.append(item_dict)
        
        # Sort genres and directors by frequency
        top_genres = sorted(favorite_genres.items(), key=lambda x: x[1], reverse=True)[:5]
        top_directors = sorted(favorite_directors.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'watched': watched,
            'want_to_watch': want_to_watch,
            'highly_rated': highly_rated,
            'poorly_rated': poorly_rated,
            'top_genres': [g[0] for g in top_genres],
            'top_directors': [d[0] for d in top_directors],
            'total_watched': len(watched),
            'content_type': content_type or 'both'
        }
    
    async def get_recommendations(
        self, 
        user_id: str, 
        db: Session,
        content_type: Optional[str] = None,
        genre_filter: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Generate movie/TV show recommendations using AI"""
        
        try:
            # Get user context
            context = self.get_user_viewing_context(user_id, db, content_type)
            
            # Build prompt
            prompt = self._build_recommendation_prompt(context, content_type, genre_filter, limit)
            
            # Try different AI providers
            recommendations = None
            provider_used = None
            
            if self.perplexity_api_key:
                try:
                    recommendations = await self._get_perplexity_recommendations(prompt)
                    provider_used = "perplexity"
                except Exception as e:
                    logger.error(f"Perplexity API error: {e}")
            
            if not recommendations and self.anthropic_api_key:
                try:
                    recommendations = await self._get_claude_recommendations(prompt)
                    provider_used = "claude"
                except Exception as e:
                    logger.error(f"Claude API error: {e}")
            
            if not recommendations and self.groq_api_key:
                try:
                    recommendations = await self._get_groq_recommendations(prompt)
                    provider_used = "groq"
                except Exception as e:
                    logger.error(f"Groq API error: {e}")
            
            if not recommendations:
                logger.warning("No AI providers available or all failed")
                return {
                    'success': False,
                    'error': 'No AI providers available',
                    'recommendations': []
                }
            
            return {
                'success': True,
                'recommendations': recommendations,
                'provider': provider_used,
                'context': {
                    'total_watched': context['total_watched'],
                    'top_genres': context['top_genres'],
                    'content_type': content_type or 'both'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': []
            }
    
    def _build_recommendation_prompt(
        self, 
        context: Dict[str, Any], 
        content_type: Optional[str],
        genre_filter: Optional[str],
        limit: int
    ) -> str:
        """Build the prompt for AI recommendation services"""
        
        content_type_str = "movies and TV shows"
        if content_type == 'movie':
            content_type_str = "movies"
        elif content_type == 'tv':
            content_type_str = "TV shows"
        
        prompt = f"""Based on the user's viewing history, recommend {limit} {content_type_str} they might enjoy.

User's Viewing Profile:
- Total watched: {context['total_watched']}
- Favorite genres: {', '.join(context['top_genres']) if context['top_genres'] else 'Various'}
- Favorite directors: {', '.join(context['top_directors'][:3]) if context['top_directors'] else 'Various'}

"""
        
        if context['highly_rated']:
            prompt += f"\nHighly rated (4-5 stars):\n"
            for item in context['highly_rated'][:10]:
                prompt += f"- {item['title']} ({item['genre'] or 'Unknown genre'})"
                if item['rating']:
                    prompt += f" - {item['rating']} stars"
                prompt += "\n"
        
        if context['poorly_rated']:
            prompt += f"\nPoorly rated (1-2 stars) - AVOID similar content:\n"
            for item in context['poorly_rated'][:5]:
                prompt += f"- {item['title']} ({item['genre'] or 'Unknown genre'})"
                if item['rating']:
                    prompt += f" - {item['rating']} stars"
                prompt += "\n"
        
        if context['want_to_watch']:
            prompt += f"\nAlready on watchlist (don't recommend these):\n"
            for item in context['want_to_watch'][:10]:
                prompt += f"- {item['title']}\n"
        
        if genre_filter:
            prompt += f"\nFocus on {genre_filter} genre.\n"
        
        prompt += f"""
Please provide {limit} {content_type_str} recommendations in JSON format. Each recommendation should include:
- title: The exact title
- year: Release year (movies) or first air year (TV shows)
- genre: Primary genre(s)
- director: Director name (for movies) or creator (for TV shows)
- description: Brief description (2-3 sentences)
- why_recommended: Why this matches the user's taste (1-2 sentences)
- content_type: "movie" or "tv_show"

Return ONLY a JSON array with no additional text or formatting."""
        
        return prompt
    
    async def _get_claude_recommendations(self, prompt: str) -> List[Dict[str, Any]]:
        """Get recommendations from Claude AI"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text.strip()
        
        # Extract JSON from response
        try:
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            recommendations = json.loads(content.strip())
            return recommendations
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response content: {content}")
            return []
    
    async def _get_perplexity_recommendations(self, prompt: str) -> List[Dict[str, Any]]:
        """Get recommendations from Perplexity AI"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Extract JSON from response
        try:
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            recommendations = json.loads(content.strip())
            return recommendations
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Perplexity response as JSON: {e}")
            logger.error(f"Response content: {content}")
            return []
    
    async def _get_groq_recommendations(self, prompt: str) -> List[Dict[str, Any]]:
        """Get recommendations from Groq"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Extract JSON from response
        try:
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            recommendations = json.loads(content.strip())
            return recommendations
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            logger.error(f"Response content: {content}")
            return []


# Create singleton instance
movie_recommendation_service = MovieRecommendationService()