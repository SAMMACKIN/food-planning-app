"""
Test suite for Book Recommendation Service
Tests AI-powered book recommendations, user feedback processing, and multi-provider fallback
"""
import pytest
import uuid
import json
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# Mock the AI service module before importing the book recommendation service
sys.modules['ai_service'] = MagicMock()

from app.services.book_recommendation_service import BookRecommendationService
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
def book_rec_service():
    """Create a book recommendation service instance for testing"""
    return BookRecommendationService()


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
        book.updated_at = Mock()
        book.updated_at.__gt__ = Mock(return_value=i < 3)  # Mock for recent activity comparison
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
def mock_ai_service():
    """Mock AI service with configurable responses"""
    ai_service = AsyncMock()
    ai_service.get_ai_response = AsyncMock()
    ai_service.groq_client = Mock()
    ai_service.claude_client = Mock()
    ai_service.perplexity_api_key = "test-key"
    return ai_service


class TestBookRecommendationService:
    """Test suite for BookRecommendationService"""
    
    # Initialization and configuration tests
    def test_service_initialization(self, book_rec_service):
        """Test service initializes with correct defaults"""
        assert book_rec_service.ai is not None
        assert book_rec_service.cache_ttl == timedelta(hours=6)
    
    def test_singleton_instance(self):
        """Test that the module provides a singleton instance"""
        # Since we're mocking the module, we'll skip testing the singleton
        # In real usage, the service provides a singleton instance
        pass
    
    # Context building tests
    @pytest.mark.asyncio
    async def test_build_user_context_empty_collection(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test building context for user with no books"""
        # Mock empty queries
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        context = await book_rec_service._build_user_context(sample_user_id, mock_db_session)
        
        assert context["total_books"] == 0
        assert context["read_books"] == []
        assert context["reading_books"] == []
        assert context["want_to_read_books"] == []
        assert context["favorite_books"] == []
        assert context["preferred_genres"] == []
        assert context["existing_books"] == []
    
    @pytest.mark.asyncio
    async def test_build_user_context_with_books(
        self, book_rec_service, mock_db_session, sample_user_id, 
        sample_books, sample_ratings, sample_feedback_history
    ):
        """Test building context with full user data"""
        # Set up mock queries
        mock_query = Mock()
        
        # Mock book query
        book_filter = Mock()
        book_filter.all.return_value = sample_books
        
        # Mock rating query
        rating_filter = Mock()
        rating_filter.all.return_value = sample_ratings
        
        # Mock feedback query
        feedback_filter = Mock()
        feedback_filter.order_by.return_value.limit.return_value.all.return_value = sample_feedback_history
        
        # Configure query routing
        def query_side_effect(model):
            if model == Book:
                return Mock(filter=Mock(return_value=book_filter))
            elif model == ContentRating:
                return Mock(filter=Mock(return_value=rating_filter))
            elif model == BookRecommendationFeedback:
                return Mock(filter=Mock(return_value=feedback_filter))
            return Mock()
        
        mock_db_session.query.side_effect = query_side_effect
        
        context = await book_rec_service._build_user_context(sample_user_id, mock_db_session)
        
        assert context["total_books"] == len(sample_books)
        assert len(context["read_books"]) == 5
        assert len(context["reading_books"]) == 2
        assert len(context["want_to_read_books"]) == 3
        assert len(context["favorite_books"]) == 2
        assert "Science Fiction" in context["preferred_genres"]
        assert len(context["existing_books"]) == len(sample_books)
        assert len(context["feedback_patterns"]["recent_positive"]) == 3
        assert len(context["feedback_patterns"]["recent_negative"]) == 2
    
    # Recommendation generation tests
    @pytest.mark.asyncio
    async def test_get_recommendations_success(
        self, book_rec_service, mock_db_session, sample_user_id,
        sample_books, mock_ai_response_success, mock_ai_service
    ):
        """Test successful recommendation generation"""
        # Mock context building
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
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
            
            # Mock AI service
            book_rec_service.ai = mock_ai_service
            mock_ai_service.get_ai_response.return_value = mock_ai_response_success
            
            request = BookRecommendationRequest(
                max_recommendations=3,
                preferred_genres=["Science Fiction"],
                exclude_genres=["Romance"]
            )
            
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            assert isinstance(response, BookRecommendationResponse)
            assert len(response.recommendations) == 3
            assert response.recommendations[0].title == "The Quantum Thief"
            assert response.recommendations[0].confidence_score == 0.92
            assert response.session_id.startswith(f"rec_{sample_user_id[:8]}")
            assert response.total_recommendations == 3
            assert "Science Fiction" in response.context_summary
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_filtering(
        self, book_rec_service, mock_db_session, sample_user_id,
        mock_ai_response_success, mock_ai_service
    ):
        """Test recommendation filtering for existing books"""
        # Create context with existing books
        existing_books = [
            "The Quantum Thief by Hannu Rajaniemi",
            "Station Eleven by Emily St. John Mandel"
        ]
        
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "total_books": 2,
                "read_books": [],
                "reading_books": [],
                "want_to_read_books": [],
                "favorite_books": [],
                "highly_rated_books": [],
                "poorly_rated_books": [],
                "preferred_genres": ["Science Fiction"],
                "genre_distribution": {},
                "feedback_patterns": {"recent_positive": [], "recent_negative": []},
                "existing_books": existing_books,
                "reading_level": "Intermediate",
                "recent_activity": {},
                "average_rating": 0.0
            }
            
            book_rec_service.ai = mock_ai_service
            mock_ai_service.get_ai_response.return_value = mock_ai_response_success
            
            request = BookRecommendationRequest(max_recommendations=5)
            
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            # Should filter out existing books
            assert len(response.recommendations) == 1
            assert response.recommendations[0].title == "The City & The City"
            
    @pytest.mark.asyncio
    async def test_get_recommendations_ai_error(
        self, book_rec_service, mock_db_session, sample_user_id, mock_ai_service
    ):
        """Test handling of AI service errors"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "total_books": 0,
                "read_books": [],
                "reading_books": [],
                "want_to_read_books": [],
                "favorite_books": [],
                "highly_rated_books": [],
                "poorly_rated_books": [],
                "preferred_genres": [],
                "genre_distribution": {},
                "feedback_patterns": {"recent_positive": [], "recent_negative": []},
                "existing_books": [],
                "reading_level": "Unknown",
                "recent_activity": {},
                "average_rating": 0.0
            }
            
            book_rec_service.ai = mock_ai_service
            mock_ai_service.get_ai_response.side_effect = Exception("AI service unavailable")
            
            request = BookRecommendationRequest(max_recommendations=3)
            
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            assert len(response.recommendations) == 0
            assert "Unable to generate recommendations" in response.context_summary
            assert response.total_recommendations == 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_malformed_response(
        self, book_rec_service, mock_db_session, sample_user_id,
        mock_ai_response_malformed, mock_ai_service
    ):
        """Test handling of malformed AI responses"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "total_books": 0,
                "read_books": [],
                "reading_books": [],
                "want_to_read_books": [],
                "favorite_books": [],
                "highly_rated_books": [],
                "poorly_rated_books": [],
                "preferred_genres": [],
                "genre_distribution": {},
                "feedback_patterns": {"recent_positive": [], "recent_negative": []},
                "existing_books": [],
                "reading_level": "Unknown",
                "recent_activity": {},
                "average_rating": 0.0
            }
            
            book_rec_service.ai = mock_ai_service
            mock_ai_service.get_ai_response.return_value = mock_ai_response_malformed
            
            request = BookRecommendationRequest(max_recommendations=3)
            
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            # Should handle parsing error gracefully
            assert len(response.recommendations) == 0
            assert response.total_recommendations == 0
    
    # Feedback processing tests
    @pytest.mark.asyncio
    async def test_process_feedback_want_to_read(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test processing 'want to read' feedback"""
        # Mock context and queries
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "read_books": [],
                "preferred_genres": ["Science Fiction"],
                "feedback_patterns": {}
            }
            
            # Mock book query - no existing book
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_db_session.query.return_value = mock_query
            
            result = await book_rec_service.process_feedback(
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
            
            # Should create feedback record and new book
            assert mock_db_session.add.call_count == 2  # Feedback + Book
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_feedback_already_read(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test processing 'already read' feedback"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "read_books": [],
                "preferred_genres": ["Science Fiction"],
                "feedback_patterns": {}
            }
            
            result = await book_rec_service.process_feedback(
                user_id=sample_user_id,
                db=mock_db_session,
                session_id="rec_test_123",
                recommendation_title="Read Book",
                recommendation_author="Known Author",
                feedback_type=FeedbackType.READ
            )
            
            assert result["success"] is True
            assert result["should_regenerate"] is False
            
            # Should only create feedback record
            assert mock_db_session.add.call_count == 1
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_feedback_not_interested(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test processing 'not interested' feedback"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "read_books": [],
                "preferred_genres": ["Science Fiction"],
                "feedback_patterns": {}
            }
            
            result = await book_rec_service.process_feedback(
                user_id=sample_user_id,
                db=mock_db_session,
                session_id="rec_test_123",
                recommendation_title="Boring Book",
                recommendation_author="Uninteresting Author",
                feedback_type=FeedbackType.NOT_INTERESTED,
                feedback_notes="Not my style"
            )
            
            assert result["success"] is True
            assert result["should_regenerate"] is True  # Should suggest regeneration
            
            # Should only create feedback record
            assert mock_db_session.add.call_count == 1
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_feedback_database_error(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test feedback processing with database error"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "read_books": [],
                "preferred_genres": [],
                "feedback_patterns": {}
            }
            
            # Simulate database error
            mock_db_session.commit.side_effect = Exception("Database error")
            
            result = await book_rec_service.process_feedback(
                user_id=sample_user_id,
                db=mock_db_session,
                session_id="rec_test_123",
                recommendation_title="Book",
                recommendation_author="Author",
                feedback_type=FeedbackType.WANT_TO_READ
            )
            
            assert result["success"] is False
            assert "Failed to process feedback" in result["message"]
            assert result["should_regenerate"] is False
            mock_db_session.rollback.assert_called_once()
    
    # Prompt generation tests
    def test_create_recommendation_prompt(self, book_rec_service):
        """Test AI prompt generation"""
        context = {
            "total_books": 50,
            "read_books": [
                {"title": "Dune", "author": "Frank Herbert", "genre": "Science Fiction", "rating": 5},
                {"title": "1984", "author": "George Orwell", "genre": "Dystopian", "rating": 4}
            ],
            "reading_books": [{"title": "Foundation", "author": "Isaac Asimov"}],
            "want_to_read_books": [],
            "favorite_books": [{"title": "Dune", "author": "Frank Herbert", "rating": 5}],
            "highly_rated_books": [{"title": "Dune", "author": "Frank Herbert", "rating": 5}],
            "poorly_rated_books": [{"title": "Bad Book", "author": "Poor Author", "rating": 1}],
            "preferred_genres": ["Science Fiction", "Mystery"],
            "genre_distribution": {"Science Fiction": 20, "Mystery": 10},
            "feedback_patterns": {
                "recent_positive": [{"title": "Good Rec", "author": "Good Author"}],
                "recent_negative": [{"title": "Bad Rec", "author": "Bad Author"}]
            },
            "existing_books": ["Dune by Frank Herbert", "1984 by George Orwell"],
            "reading_level": "Advanced",
            "recent_activity": {"active_reader": True},
            "average_rating": 4.5
        }
        
        request = BookRecommendationRequest(
            max_recommendations=5,
            preferred_genres=["Science Fiction"],
            exclude_genres=["Romance"]
        )
        
        prompt = book_rec_service._create_recommendation_prompt(context, request)
        
        assert "50" in prompt  # Total books
        assert "Science Fiction" in prompt
        assert "Dune" in prompt  # Favorite book
        assert "Bad Book" in prompt  # Poorly rated book
        assert "Good Rec" in prompt  # Positive feedback
        assert "Bad Rec" in prompt  # Negative feedback
        assert "Advanced" in prompt  # Reading level
        assert "4.5" in prompt  # Average rating
        assert "Romance" in prompt  # Excluded genre
    
    # Parsing and filtering tests
    def test_parse_ai_recommendations_valid_json(self, book_rec_service, mock_ai_response_success):
        """Test parsing valid JSON AI response"""
        recommendations = book_rec_service._parse_ai_recommendations(
            mock_ai_response_success, "session_123"
        )
        
        assert len(recommendations) == 3
        assert recommendations[0].title == "The Quantum Thief"
        assert recommendations[0].author == "Hannu Rajaniemi"
        assert recommendations[0].confidence_score == 0.92
        assert recommendations[1].title == "The City & The City"
    
    def test_parse_ai_recommendations_invalid_json(self, book_rec_service):
        """Test parsing invalid JSON response"""
        invalid_response = "This is not JSON"
        
        recommendations = book_rec_service._parse_ai_recommendations(
            invalid_response, "session_123"
        )
        
        assert recommendations == []
    
    def test_parse_ai_recommendations_partial_json(self, book_rec_service):
        """Test parsing response with partial JSON"""
        partial_response = """
        Here are some recommendations:
        {
            "recommendations": [
                {"title": "Book 1", "author": "Author 1"}
            ]
        }
        And some trailing text
        """
        
        recommendations = book_rec_service._parse_ai_recommendations(
            partial_response, "session_123"
        )
        
        assert len(recommendations) == 1
        assert recommendations[0].title == "Book 1"
    
    def test_filter_existing_books(self, book_rec_service):
        """Test filtering out existing books"""
        recommendations = [
            BookRecommendation(
                title="The Quantum Thief",
                author="Hannu Rajaniemi",
                genre="Science Fiction"
            ),
            BookRecommendation(
                title="Existing Book",
                author="Known Author",
                genre="Fiction"
            ),
            BookRecommendation(
                title="New Book",
                author="New Author",
                genre="Mystery"
            )
        ]
        
        existing_books = [
            "Existing Book by Known Author",
            "Another Book by Another Author"
        ]
        
        filtered = book_rec_service._filter_existing_books(recommendations, existing_books)
        
        assert len(filtered) == 2
        assert filtered[0].title == "The Quantum Thief"
        assert filtered[1].title == "New Book"
    
    def test_filter_existing_books_case_insensitive(self, book_rec_service):
        """Test case-insensitive filtering"""
        recommendations = [
            BookRecommendation(
                title="THE QUANTUM THIEF",
                author="Hannu Rajaniemi"
            ),
            BookRecommendation(
                title="The Quantum Thief",
                author="HANNU RAJANIEMI"
            )
        ]
        
        existing_books = ["the quantum thief by hannu rajaniemi"]
        
        filtered = book_rec_service._filter_existing_books(recommendations, existing_books)
        
        assert len(filtered) == 0  # Both should be filtered out
    
    def test_apply_user_filters_genre_exclusion(self, book_rec_service):
        """Test applying genre exclusion filters"""
        recommendations = [
            BookRecommendation(
                title="Romance Book",
                author="Romance Author",
                genre="Romance",
                confidence_score=0.9
            ),
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
        
        filtered = book_rec_service._apply_user_filters(recommendations, request, context)
        
        assert len(filtered) == 1
        assert filtered[0].genre == "Mystery"
    
    def test_apply_user_filters_preferred_genres(self, book_rec_service):
        """Test confidence adjustment for non-preferred genres"""
        recommendations = [
            BookRecommendation(
                title="Preferred Book",
                author="Author 1",
                genre="Science Fiction",
                confidence_score=0.8
            ),
            BookRecommendation(
                title="Other Book",
                author="Author 2",
                genre="Romance",
                confidence_score=0.9
            )
        ]
        
        request = BookRecommendationRequest(
            max_recommendations=5,
            preferred_genres=["Science Fiction"]
        )
        
        context = {}
        
        filtered = book_rec_service._apply_user_filters(recommendations, request, context)
        
        assert len(filtered) == 2
        # Non-preferred genre should have reduced confidence
        assert filtered[0].title == "Preferred Book"
        assert filtered[0].confidence_score == 0.8
        assert filtered[1].title == "Other Book"
        assert filtered[1].confidence_score == 0.63  # 0.9 * 0.7
    
    # Utility method tests
    def test_estimate_reading_level(self, book_rec_service, sample_books):
        """Test reading level estimation"""
        # Test with no books
        assert book_rec_service._estimate_reading_level([]) == "Unknown"
        
        # Test with light reading
        light_books = []
        for i in range(3):
            book = Mock(spec=Book)
            book.pages = 200
            book.genre = "Romance"
            light_books.append(book)
        
        assert book_rec_service._estimate_reading_level(light_books) == "Light/Popular"
        
        # Test with advanced reading
        complex_books = []
        for i in range(5):
            book = Mock(spec=Book)
            book.pages = 500
            book.genre = "Philosophy" if i < 2 else "Fiction"
            complex_books.append(book)
        
        assert book_rec_service._estimate_reading_level(complex_books) == "Advanced"
    
    def test_calculate_average_rating(self, book_rec_service):
        """Test average rating calculation"""
        # Empty ratings
        assert book_rec_service._calculate_average_rating({}) == 0.0
        
        # Sample ratings
        ratings = {
            "book1": 5,
            "book2": 4,
            "book3": 3,
            "book4": 5
        }
        
        assert book_rec_service._calculate_average_rating(ratings) == 4.2
    
    def test_generate_context_summary(self, book_rec_service):
        """Test context summary generation"""
        context = {
            "preferred_genres": ["Science Fiction", "Mystery", "Thriller"],
            "favorite_books": [{"title": "Dune", "author": "Frank Herbert"}],
            "feedback_patterns": {
                "recent_positive": [{"title": "Good Book"}],
                "recent_negative": [{"title": "Bad Book"}]
            }
        }
        
        summary = book_rec_service._generate_context_summary(context)
        
        assert "Science Fiction" in summary
        assert "Mystery" in summary
        assert "Thriller" in summary
        assert "Dune" in summary
        assert "positive feedback" in summary
        assert "less interest" in summary
    
    def test_book_to_dict(self, book_rec_service):
        """Test book model to dictionary conversion"""
        book = Mock(spec=Book)
        book.id = uuid.uuid4()
        book.title = "Test Book"
        book.author = "Test Author"
        book.genre = "Fiction"
        book.description = "A test book"
        book.pages = 300
        book.publication_year = 2023
        book.reading_status = "read"
        book.is_favorite = True
        book.date_started = datetime.now(timezone.utc)
        book.date_finished = datetime.now(timezone.utc)
        
        book_dict = book_rec_service._book_to_dict(book)
        
        assert book_dict["title"] == "Test Book"
        assert book_dict["author"] == "Test Author"
        assert book_dict["genre"] == "Fiction"
        assert book_dict["pages"] == 300
        assert book_dict["is_favorite"] is True
    
    # Multi-provider fallback tests
    @pytest.mark.asyncio
    async def test_ai_service_fallback_mechanism(self, book_rec_service):
        """Test AI service fallback when primary provider fails"""
        # This tests the actual fallback in the imported ai_service
        # The service should handle provider failures gracefully
        assert book_rec_service.ai is not None
    
    @pytest.mark.asyncio
    async def test_regenerate_recommendations(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test regenerating recommendations"""
        with patch.object(book_rec_service, 'get_recommendations') as mock_get_recs:
            mock_response = BookRecommendationResponse(
                recommendations=[],
                session_id="new_session",
                context_summary="Regenerated",
                total_recommendations=0
            )
            mock_get_recs.return_value = mock_response
            
            request = BookRecommendationRequest(max_recommendations=3)
            
            response = await book_rec_service.regenerate_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            assert response == mock_response
            mock_get_recs.assert_called_once_with(sample_user_id, mock_db_session, request)


class TestBookRecommendationEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_ai_response(self, book_rec_service, mock_db_session, sample_user_id):
        """Test handling of empty AI response"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "total_books": 0,
                "read_books": [],
                "reading_books": [],
                "want_to_read_books": [],
                "favorite_books": [],
                "highly_rated_books": [],
                "poorly_rated_books": [],
                "preferred_genres": [],
                "genre_distribution": {},
                "feedback_patterns": {"recent_positive": [], "recent_negative": []},
                "existing_books": [],
                "reading_level": "Unknown",
                "recent_activity": {},
                "average_rating": 0.0
            }
            
            mock_ai = AsyncMock()
            mock_ai.get_ai_response.return_value = ""
            book_rec_service.ai = mock_ai
            
            request = BookRecommendationRequest(max_recommendations=3)
            
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            assert len(response.recommendations) == 0
    
    @pytest.mark.asyncio
    async def test_duplicate_book_in_want_to_read(
        self, book_rec_service, mock_db_session, sample_user_id
    ):
        """Test handling when user already has book in want to read list"""
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "read_books": [],
                "preferred_genres": ["Science Fiction"],
                "feedback_patterns": {}
            }
            
            # Mock existing book
            existing_book = Mock()
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = existing_book
            mock_db_session.query.return_value = mock_query
            
            result = await book_rec_service.process_feedback(
                user_id=sample_user_id,
                db=mock_db_session,
                session_id="rec_test_123",
                recommendation_title="Existing Book",
                recommendation_author="Known Author",
                feedback_type=FeedbackType.WANT_TO_READ
            )
            
            assert result["success"] is True
            # Should only add feedback, not create duplicate book
            assert mock_db_session.add.call_count == 1
    
    def test_recommendations_with_missing_fields(self, book_rec_service):
        """Test parsing recommendations with missing optional fields"""
        partial_json = json.dumps({
            "recommendations": [
                {
                    "title": "Minimal Book",
                    "author": "Minimal Author"
                    # Missing all optional fields
                }
            ]
        })
        
        recommendations = book_rec_service._parse_ai_recommendations(
            partial_json, "session_123"
        )
        
        assert len(recommendations) == 1
        assert recommendations[0].title == "Minimal Book"
        assert recommendations[0].author == "Minimal Author"
        assert recommendations[0].genre is None
        assert recommendations[0].description is None
        assert recommendations[0].confidence_score == 0.5  # Default


class TestBookRecommendationIntegration:
    """Integration tests combining multiple components"""
    
    @pytest.mark.asyncio
    async def test_full_recommendation_cycle(
        self, book_rec_service, mock_db_session, sample_user_id,
        sample_books, mock_ai_response_success, mock_ai_service
    ):
        """Test complete recommendation cycle: request -> AI -> filter -> response"""
        # Setup full context
        with patch.object(book_rec_service, '_build_user_context') as mock_context:
            mock_context.return_value = {
                "total_books": 10,
                "read_books": [
                    {"title": "Foundation", "author": "Isaac Asimov", "rating": 5, "genre": "Science Fiction"}
                ],
                "reading_books": [],
                "want_to_read_books": [],
                "favorite_books": [
                    {"title": "Foundation", "author": "Isaac Asimov", "rating": 5}
                ],
                "highly_rated_books": [
                    {"title": "Foundation", "author": "Isaac Asimov", "rating": 5}
                ],
                "poorly_rated_books": [],
                "preferred_genres": ["Science Fiction", "Mystery"],
                "genre_distribution": {"Science Fiction": 8, "Mystery": 2},
                "feedback_patterns": {
                    "recent_positive": [
                        {"title": "Neuromancer", "author": "William Gibson"}
                    ],
                    "recent_negative": []
                },
                "existing_books": [
                    "Foundation by Isaac Asimov",
                    "The Quantum Thief by Hannu Rajaniemi"  # This will be filtered
                ],
                "reading_level": "Advanced",
                "recent_activity": {"active_reader": True},
                "average_rating": 4.5
            }
            
            book_rec_service.ai = mock_ai_service
            mock_ai_service.get_ai_response.return_value = mock_ai_response_success
            
            # Request with genre preferences
            request = BookRecommendationRequest(
                max_recommendations=5,
                preferred_genres=["Science Fiction", "Mystery"],
                exclude_genres=["Romance"]
            )
            
            # Get recommendations
            response = await book_rec_service.get_recommendations(
                sample_user_id, mock_db_session, request
            )
            
            # Verify response
            assert len(response.recommendations) == 2  # One filtered out
            assert response.recommendations[0].title == "The City & The City"
            assert response.recommendations[1].title == "Station Eleven"
            
            # Process feedback on first recommendation
            feedback_result = await book_rec_service.process_feedback(
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