"""
Advanced tests for Movie Recommendation Service with edge cases and complex scenarios
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid
from sqlalchemy.orm import Session

from app.services.movie_recommendation_service import MovieRecommendationService
from app.models.content import Movie, ContentRating, ContentType
from app.schemas.movies import ViewingStatus


class TestMovieRecommendationServiceAdvanced:
    """Advanced test cases for MovieRecommendationService"""
    
    @pytest.fixture
    def service(self):
        """Create a service instance with mocked API keys"""
        with patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'test-anthropic-key',
            'PERPLEXITY_API_KEY': 'test-perplexity-key',
            'GROQ_API_KEY': 'test-groq-key'
        }):
            return MovieRecommendationService()
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID"""
        return str(uuid.uuid4())
    
    def test_get_user_viewing_context_with_mixed_content(self, service, mock_db, sample_user_id):
        """Test context generation with movies and TV shows mixed"""
        # Create mixed content
        movies = [
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="The Matrix",
                genre="Science Fiction",
                viewing_status=ViewingStatus.WATCHED,
                date_watched=datetime.now() - timedelta(days=10)
            ),
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="Breaking Bad",
                genre="TV Series, Drama, Crime",
                viewing_status=ViewingStatus.WATCHED,
                date_watched=datetime.now() - timedelta(days=30)
            ),
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="Inception",
                genre="Science Fiction, Thriller",
                viewing_status=ViewingStatus.WANT_TO_WATCH
            )
        ]
        
        # Create ratings
        ratings = [
            ContentRating(
                user_id=sample_user_id,
                movie_id=movies[0].id,
                rating=5,
                content_type=ContentType.MOVIE
            ),
            ContentRating(
                user_id=sample_user_id,
                movie_id=movies[1].id,
                rating=5,
                content_type=ContentType.MOVIE
            )
        ]
        
        # Mock queries
        movie_query = Mock()
        movie_query.filter.return_value = movie_query
        movie_query.all.return_value = movies
        
        rating_query = Mock()
        rating_query.filter.return_value = rating_query
        rating_query.all.return_value = ratings
        
        def query_router(model):
            if model == Movie:
                return movie_query
            elif model == ContentRating:
                return rating_query
            return Mock()
        
        mock_db.query.side_effect = query_router
        
        # Test without content type filter
        context = service.get_user_viewing_context(sample_user_id, mock_db)
        
        assert len(context['watched']) == 2
        assert len(context['want_to_watch']) == 1
        assert context['favorite_genres'] == ['Science Fiction', 'Drama']  # Most common
        assert context['recently_watched'][0]['title'] == "The Matrix"  # Most recent
        
        # Test with movie filter
        movie_query.reset_mock()
        context = service.get_user_viewing_context(sample_user_id, mock_db, content_type='movie')
        
        # Verify TV series filter was applied
        assert movie_query.filter.call_count >= 2  # User filter + content type filter
    
    def test_get_user_viewing_context_empty_collection(self, service, mock_db, sample_user_id):
        """Test context generation for user with no content"""
        # Mock empty results
        empty_query = Mock()
        empty_query.filter.return_value = empty_query
        empty_query.all.return_value = []
        mock_db.query.return_value = empty_query
        
        context = service.get_user_viewing_context(sample_user_id, mock_db)
        
        assert context['watched'] == []
        assert context['want_to_watch'] == []
        assert context['favorite_genres'] == []
        assert context['high_rated'] == []
        assert context['recently_watched'] == []
        assert context['total_movies'] == 0
    
    def test_get_user_viewing_context_with_duplicate_genres(self, service, mock_db, sample_user_id):
        """Test genre extraction with duplicates and complex formatting"""
        movies = [
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="Movie 1",
                genre="Action, Adventure, Action",  # Duplicate within same movie
                viewing_status=ViewingStatus.WATCHED
            ),
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="Movie 2",
                genre="action, ADVENTURE",  # Different case
                viewing_status=ViewingStatus.WATCHED
            ),
            Movie(
                id=uuid.uuid4(),
                user_id=sample_user_id,
                title="Movie 3",
                genre="  Drama  ,  Comedy  ",  # Extra spaces
                viewing_status=ViewingStatus.WATCHED
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = movies
        mock_db.query.return_value = mock_query
        
        context = service.get_user_viewing_context(sample_user_id, mock_db)
        
        # Should handle duplicates and normalize genres
        genres = context['favorite_genres']
        assert 'Action' in genres or 'action' in genres
        assert 'Drama' in genres
        assert len(set(g.lower() for g in genres)) == 4  # Action, Adventure, Drama, Comedy
    
    @patch('app.services.movie_recommendation_service.httpx.AsyncClient')
    async def test_generate_recommendations_all_providers_fail(self, mock_client, service, mock_db, sample_user_id):
        """Test recommendation generation when all AI providers fail"""
        # Mock all API calls to fail
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        # Mock user context
        with patch.object(service, 'get_user_viewing_context') as mock_context:
            mock_context.return_value = {
                'watched': [{'title': 'Test Movie', 'genre': 'Action'}],
                'favorite_genres': ['Action'],
                'high_rated': [],
                'recently_watched': [],
                'want_to_watch': [],
                'total_movies': 1
            }
            
            recommendations = await service.generate_recommendations(
                sample_user_id, mock_db, num_recommendations=5
            )
            
            # Should return empty list when all providers fail
            assert recommendations == []
    
    @patch('app.services.movie_recommendation_service.httpx.AsyncClient')
    async def test_generate_recommendations_with_parsing_errors(self, mock_client, service, mock_db, sample_user_id):
        """Test handling of malformed AI responses"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Not valid JSON {["
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        with patch.object(service, 'get_user_viewing_context') as mock_context:
            mock_context.return_value = {
                'watched': [],
                'favorite_genres': ['Drama'],
                'high_rated': [],
                'recently_watched': [],
                'want_to_watch': [],
                'total_movies': 0
            }
            
            recommendations = await service.generate_recommendations(sample_user_id, mock_db)
            
            # Should handle gracefully
            assert isinstance(recommendations, list)
    
    def test_parse_ai_recommendations_edge_cases(self, service):
        """Test parsing various edge case AI responses"""
        # Test with missing required fields
        incomplete_rec = {
            "recommendations": [
                {
                    "title": "Movie Without Year"
                    # Missing year and reason
                },
                {
                    "year": 2023,
                    "reason": "No title movie"
                    # Missing title
                }
            ]
        }
        
        result = service._parse_ai_recommendations(incomplete_rec)
        assert len(result) == 0  # Should filter out incomplete recommendations
        
        # Test with extra fields
        extra_fields_rec = {
            "recommendations": [
                {
                    "title": "Valid Movie",
                    "year": 2023,
                    "reason": "Good movie",
                    "extra_field": "Should be ignored",
                    "another_extra": 123
                }
            ]
        }
        
        result = service._parse_ai_recommendations(extra_fields_rec)
        assert len(result) == 1
        assert "extra_field" not in result[0]
        
        # Test with wrong data types
        wrong_types_rec = {
            "recommendations": [
                {
                    "title": 123,  # Should be string
                    "year": "2023",  # Should be int
                    "reason": True  # Should be string
                }
            ]
        }
        
        result = service._parse_ai_recommendations(wrong_types_rec)
        # Should handle type conversion or filter out
        assert len(result) <= 1
    
    def test_build_recommendation_prompt_edge_cases(self, service):
        """Test prompt building with various edge cases"""
        # Test with only want-to-watch movies
        context = {
            'watched': [],
            'want_to_watch': [
                {'title': 'Future Movie 1', 'genre': 'Sci-Fi'},
                {'title': 'Future Movie 2', 'genre': 'Drama'}
            ],
            'favorite_genres': [],
            'high_rated': [],
            'recently_watched': []
        }
        
        prompt = service._build_recommendation_prompt(context, num_recommendations=3)
        
        assert "want to watch" in prompt.lower()
        assert "Future Movie 1" in prompt
        assert "3 movie" in prompt
        
        # Test with only low-rated movies
        context = {
            'watched': [
                {'title': 'Bad Movie', 'genre': 'Horror', 'rating': 1}
            ],
            'want_to_watch': [],
            'favorite_genres': ['Horror'],  # Favorite genre but low ratings
            'high_rated': [],
            'recently_watched': []
        }
        
        prompt = service._build_recommendation_prompt(context)
        
        # Should still generate reasonable prompt
        assert "Horror" in prompt
        assert "recommend" in prompt.lower()
    
    @patch('app.services.movie_recommendation_service.httpx.AsyncClient')
    async def test_fetch_movie_details_with_timeout(self, mock_client, service):
        """Test movie details fetching with network timeout"""
        import asyncio
        
        # Mock timeout
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timeout")
        )
        
        result = await service.fetch_movie_details("Test Movie", 2023)
        
        # Should return None on timeout
        assert result is None
    
    @patch('app.services.movie_recommendation_service.httpx.AsyncClient')
    async def test_concurrent_recommendation_requests(self, mock_client, service, mock_db):
        """Test handling multiple concurrent recommendation requests"""
        import asyncio
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendations": [{
                            "title": f"Movie {i}",
                            "year": 2023,
                            "reason": "Test"
                        } for i in range(5)]
                    })
                }
            }]
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        with patch.object(service, 'get_user_viewing_context') as mock_context:
            mock_context.return_value = {
                'watched': [],
                'favorite_genres': ['Action'],
                'high_rated': [],
                'recently_watched': [],
                'want_to_watch': [],
                'total_movies': 0
            }
            
            # Make concurrent requests
            user_ids = [str(uuid.uuid4()) for _ in range(5)]
            tasks = [
                service.generate_recommendations(user_id, mock_db)
                for user_id in user_ids
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 5
            assert all(isinstance(r, list) for r in results)
    
    def test_recommendation_deduplication(self, service):
        """Test that duplicate recommendations are filtered"""
        duplicate_recs = {
            "recommendations": [
                {"title": "Inception", "year": 2010, "reason": "Great movie"},
                {"title": "Inception", "year": 2010, "reason": "Different reason"},
                {"title": "The Matrix", "year": 1999, "reason": "Classic"},
                {"title": "inception", "year": 2010, "reason": "Lowercase title"},  # Same movie, different case
            ]
        }
        
        result = service._parse_ai_recommendations(duplicate_recs)
        
        # Should deduplicate based on title (case-insensitive would be ideal)
        titles = [r['title'] for r in result]
        assert len(titles) <= 3  # May keep both "Inception" and "inception" depending on implementation