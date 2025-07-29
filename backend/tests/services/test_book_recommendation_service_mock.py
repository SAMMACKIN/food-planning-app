"""
Test suite for Book Recommendation Service with full mocking
Tests AI-powered book recommendations, user feedback processing, and multi-provider fallback
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock, create_autospec
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.books import (
    BookRecommendation,
    BookRecommendationRequest, 
    BookRecommendationResponse,
    FeedbackType
)
from app.models.content import Book, BookRecommendationFeedback, ContentRating


# Test fixtures and mock data
@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "test-user-123"


@pytest.fixture
def sample_books():
    """Sample book collection for a user"""
    books = []
    # Read books
    for i in range(5):
        book = Mock(spec=Book)
        book.id = uuid.uuid4()
        book.title = f"Read Book {i}"
        book.author = f"Author {i}"
        book.genre = ["Fiction", "Science Fiction", "Mystery", "Romance", "Thriller"][i]
        book.reading_status = "read"
        book.is_favorite = i < 2
        book.pages = 300 + (i * 50)
        book.publication_year = 2020 + i
        book.updated_at = datetime.now(timezone.utc) - timedelta(days=i*10)
        books.append(book)
    
    # Currently reading books
    for i in range(2):
        book = Mock(spec=Book)
        book.id = uuid.uuid4()
        book.title = f"Reading Book {i}"
        book.author = f"Current Author {i}"
        book.genre = "Science Fiction"
        book.reading_status = "reading"
        book.is_favorite = False
        book.pages = 400
        books.append(book)
    
    # Want to read books
    for i in range(3):
        book = Mock(spec=Book)
        book.id = uuid.uuid4()
        book.title = f"Want to Read Book {i}"
        book.author = f"Future Author {i}"
        book.genre = "Mystery"
        book.reading_status = "want_to_read"
        book.is_favorite = False
        book.pages = 250
        books.append(book)
    
    return books


@pytest.fixture
def sample_ratings():
    """Sample book ratings"""
    ratings = []
    for i in range(5):
        rating = Mock(spec=ContentRating)
        rating.book_id = uuid.uuid4()
        rating.rating = [5, 4, 4, 2, 1][i]  # Mix of high and low ratings
        rating.user_id = "test-user-123"
        ratings.append(rating)
    return ratings


@pytest.fixture
def sample_feedback_history():
    """Sample recommendation feedback history"""
    feedback_list = []
    
    # Positive feedback
    for i in range(3):
        feedback = Mock(spec=BookRecommendationFeedback)
        feedback.id = uuid.uuid4()
        feedback.user_id = "test-user-123"
        feedback.recommendation_session_id = f"rec_test_{i}"
        feedback.recommended_title = f"Liked Book {i}"
        feedback.recommended_author = f"Liked Author {i}"
        feedback.feedback_type = "want_to_read"
        feedback.created_at = datetime.now(timezone.utc) - timedelta(days=i)
        feedback_list.append(feedback)
    
    # Negative feedback
    for i in range(2):
        feedback = Mock(spec=BookRecommendationFeedback)
        feedback.id = uuid.uuid4()
        feedback.user_id = "test-user-123"
        feedback.recommendation_session_id = f"rec_test_neg_{i}"
        feedback.recommended_title = f"Disliked Book {i}"
        feedback.recommended_author = f"Disliked Author {i}"
        feedback.feedback_type = "not_interested"
        feedback.created_at = datetime.now(timezone.utc) - timedelta(days=i+3)
        feedback_list.append(feedback)
    
    return feedback_list


@pytest.fixture
def mock_ai_response_success():
    """Mock successful AI response with book recommendations"""
    return json.dumps({
        "recommendations": [
            {
                "title": "The Quantum Thief",
                "author": "Hannu Rajaniemi",
                "genre": "Science Fiction",
                "description": "A post-human heist story set in a solar system where reality is negotiable.",
                "reasoning": "Based on your interest in science fiction and high ratings for complex narratives.",
                "publication_year": 2010,
                "pages": 336,
                "confidence_score": 0.92
            },
            {
                "title": "The City & The City",
                "author": "China Miéville",
                "genre": "Mystery",
                "description": "A murder mystery set in two overlapping cities that exist in the same space.",
                "reasoning": "Combines your love of mystery with science fiction elements.",
                "publication_year": 2009,
                "pages": 312,
                "confidence_score": 0.88
            },
            {
                "title": "Station Eleven",
                "author": "Emily St. John Mandel",
                "genre": "Fiction",
                "description": "A haunting story about a traveling Shakespeare troupe in a post-pandemic world.",
                "reasoning": "Literary fiction with elements that match your highly-rated books.",
                "publication_year": 2014,
                "pages": 333,
                "confidence_score": 0.85
            }
        ]
    })


@pytest.fixture
def mock_ai_response_malformed():
    """Mock malformed AI response"""
    return "Here are some book recommendations: The Quantum Thief, Station Eleven..."


@pytest.fixture
def mock_book_rec_service():
    """Create a fully mocked book recommendation service"""
    service = Mock()
    service.ai = AsyncMock()
    service.cache_ttl = timedelta(hours=6)
    
    # Mock methods
    service._build_user_context = AsyncMock()
    service._create_recommendation_prompt = Mock()
    service._parse_ai_recommendations = Mock()
    service._filter_existing_books = Mock()
    service._apply_user_filters = Mock()
    service._generate_context_summary = Mock()
    service._book_to_dict = Mock()
    service._estimate_reading_level = Mock()
    service._get_recent_activity = Mock()
    service._calculate_average_rating = Mock()
    service.get_recommendations = AsyncMock()
    service.process_feedback = AsyncMock()
    service.regenerate_recommendations = AsyncMock()
    
    return service


class TestBookRecommendationServiceMocked:
    """Test suite for BookRecommendationService with full mocking"""
    
    # Recommendation generation tests
    @pytest.mark.asyncio
    async def test_get_recommendations_success(
        self, mock_book_rec_service, mock_db_session, sample_user_id,
        sample_books, mock_ai_response_success
    ):
        """Test successful recommendation generation"""
        # Setup mock returns
        context = {
            "total_books": 10,
            "read_books": [{"title": "Test Book", "author": "Test Author", "rating": 5}],
            "reading_books": [],
            "want_to_read_books": [],
            "favorite_books": [],
            "highly_rated_books": [],
            "poorly_rated_books": [],
            "preferred_genres": ["Science Fiction", "Mystery"],
            "genre_distribution": {"Science Fiction": 5, "Mystery": 3},
            "feedback_patterns": {"recent_positive": [], "recent_negative": []},
            "existing_books": ["Test Book by Test Author"],
            "reading_level": "Intermediate",
            "recent_activity": {"active_reader": True},
            "average_rating": 4.2
        }
        
        mock_book_rec_service._build_user_context.return_value = context
        mock_book_rec_service.ai.get_ai_response.return_value = mock_ai_response_success
        
        recommendations = [
            BookRecommendation(
                title="The Quantum Thief",
                author="Hannu Rajaniemi",
                genre="Science Fiction",
                description="A post-human heist story.",
                confidence_score=0.92
            ),
            BookRecommendation(
                title="The City & The City",
                author="China Miéville",
                genre="Mystery",
                description="A murder mystery.",
                confidence_score=0.88
            )
        ]
        
        mock_book_rec_service._parse_ai_recommendations.return_value = recommendations
        mock_book_rec_service._filter_existing_books.return_value = recommendations
        mock_book_rec_service._apply_user_filters.return_value = recommendations
        mock_book_rec_service._generate_context_summary.return_value = "Based on your Science Fiction preference"
        
        # Configure the main method
        mock_book_rec_service.get_recommendations.return_value = BookRecommendationResponse(
            recommendations=recommendations,
            session_id="rec_test-user_123456",
            context_summary="Based on your Science Fiction preference",
            total_recommendations=2
        )
        
        request = BookRecommendationRequest(
            max_recommendations=3,
            preferred_genres=["Science Fiction"],
            exclude_genres=["Romance"]
        )
        
        response = await mock_book_rec_service.get_recommendations(
            sample_user_id, mock_db_session, request
        )
        
        assert isinstance(response, BookRecommendationResponse)
        assert len(response.recommendations) == 2
        assert response.recommendations[0].title == "The Quantum Thief"
        assert response.recommendations[0].confidence_score == 0.92
        assert response.total_recommendations == 2
        assert "Science Fiction" in response.context_summary
    
    @pytest.mark.asyncio
    async def test_get_recommendations_ai_error(
        self, mock_book_rec_service, mock_db_session, sample_user_id
    ):
        """Test handling of AI service errors"""
        mock_book_rec_service.get_recommendations.return_value = BookRecommendationResponse(
            recommendations=[],
            session_id="rec_test_error",
            context_summary="Unable to generate recommendations: AI service unavailable",
            total_recommendations=0
        )
        
        request = BookRecommendationRequest(max_recommendations=3)
        
        response = await mock_book_rec_service.get_recommendations(
            sample_user_id, mock_db_session, request
        )
        
        assert len(response.recommendations) == 0
        assert "Unable to generate recommendations" in response.context_summary
        assert response.total_recommendations == 0
    
    # Feedback processing tests
    @pytest.mark.asyncio
    async def test_process_feedback_want_to_read(
        self, mock_book_rec_service, mock_db_session, sample_user_id
    ):
        """Test processing 'want to read' feedback"""
        mock_book_rec_service.process_feedback.return_value = {
            "success": True,
            "message": "Feedback recorded: want_to_read",
            "should_regenerate": False
        }
        
        result = await mock_book_rec_service.process_feedback(
            user_id=sample_user_id,
            db=mock_db_session,
            session_id="rec_test_123",
            recommendation_title="New Book",
            recommendation_author="New Author",
            feedback_type=FeedbackType.WANT_TO_READ,
            feedback_notes="Looks interesting"
        )
        
        assert result["success"] is True
        assert "want_to_read" in result["message"]
        assert result["should_regenerate"] is False
    
    @pytest.mark.asyncio
    async def test_process_feedback_not_interested(
        self, mock_book_rec_service, mock_db_session, sample_user_id
    ):
        """Test processing 'not interested' feedback"""
        mock_book_rec_service.process_feedback.return_value = {
            "success": True,
            "message": "Feedback recorded: not_interested",
            "should_regenerate": True
        }
        
        result = await mock_book_rec_service.process_feedback(
            user_id=sample_user_id,
            db=mock_db_session,
            session_id="rec_test_123",
            recommendation_title="Boring Book",
            recommendation_author="Uninteresting Author",
            feedback_type=FeedbackType.NOT_INTERESTED,
            feedback_notes="Not my style"
        )
        
        assert result["success"] is True
        assert result["should_regenerate"] is True
    
    # Utility method tests
    def test_parse_ai_recommendations_valid_json(self, mock_book_rec_service, mock_ai_response_success):
        """Test parsing valid JSON AI response"""
        recommendations = [
            BookRecommendation(
                title="The Quantum Thief",
                author="Hannu Rajaniemi",
                genre="Science Fiction",
                confidence_score=0.92
            )
        ]
        
        mock_book_rec_service._parse_ai_recommendations.return_value = recommendations
        
        result = mock_book_rec_service._parse_ai_recommendations(
            mock_ai_response_success, "session_123"
        )
        
        assert len(result) == 1
        assert result[0].title == "The Quantum Thief"
    
    def test_filter_existing_books(self, mock_book_rec_service):
        """Test filtering out existing books"""
        recommendations = [
            BookRecommendation(
                title="The Quantum Thief",
                author="Hannu Rajaniemi",
                genre="Science Fiction"
            ),
            BookRecommendation(
                title="New Book",
                author="New Author",
                genre="Mystery"
            )
        ]
        
        existing_books = ["Existing Book by Known Author"]
        
        mock_book_rec_service._filter_existing_books.return_value = recommendations
        
        filtered = mock_book_rec_service._filter_existing_books(recommendations, existing_books)
        
        assert len(filtered) == 2
    
    def test_apply_user_filters_genre_exclusion(self, mock_book_rec_service):
        """Test applying genre exclusion filters"""
        recommendations = [
            BookRecommendation(
                title="Mystery Book",
                author="Mystery Author",
                genre="Mystery",
                confidence_score=0.8
            )
        ]
        
        request = BookRecommendationRequest(
            max_recommendations=5,
            exclude_genres=["Romance"]
        )
        
        context = {"preferred_genres": ["Mystery"]}
        
        mock_book_rec_service._apply_user_filters.return_value = recommendations
        
        filtered = mock_book_rec_service._apply_user_filters(recommendations, request, context)
        
        assert len(filtered) == 1
        assert filtered[0].genre == "Mystery"
    
    def test_estimate_reading_level(self, mock_book_rec_service, sample_books):
        """Test reading level estimation"""
        mock_book_rec_service._estimate_reading_level.side_effect = [
            "Unknown",
            "Light/Popular",
            "Advanced"
        ]
        
        # Test with no books
        assert mock_book_rec_service._estimate_reading_level([]) == "Unknown"
        
        # Test with light reading
        assert mock_book_rec_service._estimate_reading_level(sample_books[:3]) == "Light/Popular"
        
        # Test with advanced reading
        assert mock_book_rec_service._estimate_reading_level(sample_books) == "Advanced"
    
    def test_calculate_average_rating(self, mock_book_rec_service):
        """Test average rating calculation"""
        mock_book_rec_service._calculate_average_rating.side_effect = [0.0, 4.2]
        
        # Empty ratings
        assert mock_book_rec_service._calculate_average_rating({}) == 0.0
        
        # Sample ratings
        ratings = {
            "book1": 5,
            "book2": 4,
            "book3": 3,
            "book4": 5
        }
        
        assert mock_book_rec_service._calculate_average_rating(ratings) == 4.2
    
    def test_generate_context_summary(self, mock_book_rec_service):
        """Test context summary generation"""
        context = {
            "preferred_genres": ["Science Fiction", "Mystery", "Thriller"],
            "favorite_books": [{"title": "Dune", "author": "Frank Herbert"}],
            "feedback_patterns": {
                "recent_positive": [{"title": "Good Book"}],
                "recent_negative": [{"title": "Bad Book"}]
            }
        }
        
        mock_book_rec_service._generate_context_summary.return_value = (
            "Based on your preference for Science Fiction, Mystery, Thriller. "
            "Similar to your favorites like 'Dune'. "
            "Incorporating your recent positive feedback. "
            "Avoiding patterns you've shown less interest in."
        )
        
        summary = mock_book_rec_service._generate_context_summary(context)
        
        assert "Science Fiction" in summary
        assert "Mystery" in summary
        assert "Thriller" in summary
        assert "Dune" in summary
        assert "positive feedback" in summary
        assert "less interest" in summary


class TestBookRecommendationEdgeCasesMocked:
    """Test edge cases and error scenarios with mocking"""
    
    @pytest.mark.asyncio
    async def test_empty_ai_response(self, mock_book_rec_service, mock_db_session, sample_user_id):
        """Test handling of empty AI response"""
        mock_book_rec_service.get_recommendations.return_value = BookRecommendationResponse(
            recommendations=[],
            session_id="rec_empty",
            context_summary="No recommendations available",
            total_recommendations=0
        )
        
        request = BookRecommendationRequest(max_recommendations=3)
        
        response = await mock_book_rec_service.get_recommendations(
            sample_user_id, mock_db_session, request
        )
        
        assert len(response.recommendations) == 0
    
    def test_recommendations_with_missing_fields(self, mock_book_rec_service):
        """Test parsing recommendations with missing optional fields"""
        mock_book_rec_service._parse_ai_recommendations.return_value = [
            BookRecommendation(
                title="Minimal Book",
                author="Minimal Author",
                genre=None,
                description=None,
                confidence_score=0.5
            )
        ]
        
        recommendations = mock_book_rec_service._parse_ai_recommendations(
            '{"recommendations": [{"title": "Minimal Book", "author": "Minimal Author"}]}',
            "session_123"
        )
        
        assert len(recommendations) == 1
        assert recommendations[0].title == "Minimal Book"
        assert recommendations[0].genre is None


class TestBookRecommendationIntegrationMocked:
    """Integration tests with mocked service"""
    
    @pytest.mark.asyncio
    async def test_full_recommendation_cycle(
        self, mock_book_rec_service, mock_db_session, sample_user_id
    ):
        """Test complete recommendation cycle: request -> AI -> filter -> response"""
        # Setup initial recommendations
        initial_recs = [
            BookRecommendation(
                title="The City & The City",
                author="China Miéville",
                genre="Mystery",
                confidence_score=0.9
            ),
            BookRecommendation(
                title="Station Eleven",
                author="Emily St. John Mandel",
                genre="Fiction",
                confidence_score=0.85
            )
        ]
        
        mock_book_rec_service.get_recommendations.return_value = BookRecommendationResponse(
            recommendations=initial_recs,
            session_id="rec_cycle_test",
            context_summary="Based on your reading history",
            total_recommendations=2
        )
        
        # Request with genre preferences
        request = BookRecommendationRequest(
            max_recommendations=5,
            preferred_genres=["Science Fiction", "Mystery"],
            exclude_genres=["Romance"]
        )
        
        # Get recommendations
        response = await mock_book_rec_service.get_recommendations(
            sample_user_id, mock_db_session, request
        )
        
        # Verify response
        assert len(response.recommendations) == 2
        assert response.recommendations[0].title == "The City & The City"
        
        # Setup feedback processing
        mock_book_rec_service.process_feedback.return_value = {
            "success": True,
            "message": "Feedback recorded: want_to_read",
            "should_regenerate": False
        }
        
        # Process feedback
        feedback_result = await mock_book_rec_service.process_feedback(
            user_id=sample_user_id,
            db=mock_db_session,
            session_id=response.session_id,
            recommendation_title=response.recommendations[0].title,
            recommendation_author=response.recommendations[0].author,
            feedback_type=FeedbackType.WANT_TO_READ
        )
        
        assert feedback_result["success"] is True
        assert feedback_result["should_regenerate"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])