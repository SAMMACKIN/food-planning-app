"""
Edge case tests for Movies API
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

from app.api.movies import (
    create_movie, update_movie, delete_movie, 
    get_movies, get_movie, toggle_favorite,
    fetch_movie_details, import_from_netflix
)
from app.models.content import Movie
from app.schemas.movies import (
    MovieCreate, MovieUpdate, ViewingStatus,
    MovieFilters, MovieDetailsRequest
)


class TestMoviesAPIEdgeCases:
    """Test edge cases and error handling in Movies API"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return {
            "id": str(uuid.uuid4()),
            "email": "test@example.com"
        }
    
    @pytest.fixture
    def sample_movie_data(self):
        """Sample movie creation data"""
        return MovieCreate(
            title="Test Movie",
            description="A test movie",
            genre="Action",
            director="Test Director",
            release_year=2023,
            runtime=120,
            viewing_status=ViewingStatus.WANT_TO_WATCH
        )
    
    def test_create_movie_with_database_error(self, mock_db, mock_user, sample_movie_data):
        """Test movie creation when database commit fails"""
        # Mock database error
        mock_db.add = Mock()
        mock_db.commit.side_effect = SQLAlchemyError("Database connection lost")
        
        with pytest.raises(HTTPException) as exc_info:
            create_movie(sample_movie_data, mock_db, mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Failed to create movie" in str(exc_info.value.detail)
        assert mock_db.rollback.called
    
    def test_create_movie_with_duplicate_constraint(self, mock_db, mock_user, sample_movie_data):
        """Test movie creation with unique constraint violation"""
        mock_db.add = Mock()
        mock_db.commit.side_effect = IntegrityError(
            "duplicate key value violates unique constraint",
            None, None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            create_movie(sample_movie_data, mock_db, mock_user)
        
        assert exc_info.value.status_code == 500
        assert mock_db.rollback.called
    
    def test_create_movie_with_invalid_uuid(self, mock_db, sample_movie_data):
        """Test movie creation with invalid user ID"""
        invalid_user = {"id": "not-a-valid-uuid", "email": "test@example.com"}
        
        with pytest.raises(HTTPException) as exc_info:
            create_movie(sample_movie_data, mock_db, invalid_user)
        
        assert exc_info.value.status_code == 500
    
    def test_update_movie_not_found(self, mock_db, mock_user):
        """Test updating non-existent movie"""
        movie_id = str(uuid.uuid4())
        update_data = MovieUpdate(title="Updated Title")
        
        # Mock query returns None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            update_movie(movie_id, update_data, mock_db, mock_user)
        
        assert exc_info.value.status_code == 404
        assert "Movie not found" in str(exc_info.value.detail)
    
    def test_update_movie_wrong_user(self, mock_db, mock_user):
        """Test updating movie owned by different user"""
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # Different user
            title="Someone else's movie"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = movie
        mock_db.query.return_value = mock_query
        
        update_data = MovieUpdate(title="Hacked Title")
        
        with pytest.raises(HTTPException) as exc_info:
            update_movie(str(movie.id), update_data, mock_db, mock_user)
        
        assert exc_info.value.status_code == 404  # Should appear as not found
    
    def test_delete_movie_with_database_error(self, mock_db, mock_user):
        """Test movie deletion when database commit fails"""
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Movie to delete"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = movie
        mock_db.query.return_value = mock_query
        
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            delete_movie(str(movie.id), mock_db, mock_user)
        
        assert exc_info.value.status_code == 500
        assert mock_db.rollback.called
    
    def test_get_movies_with_invalid_pagination(self, mock_db, mock_user):
        """Test getting movies with invalid pagination parameters"""
        # Negative page
        with pytest.raises(HTTPException) as exc_info:
            get_movies(page=-1, page_size=10, db=mock_db, current_user=mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Invalid page number" in str(exc_info.value.detail)
        
        # Zero page size
        with pytest.raises(HTTPException) as exc_info:
            get_movies(page=1, page_size=0, db=mock_db, current_user=mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Invalid page size" in str(exc_info.value.detail)
        
        # Page size too large
        with pytest.raises(HTTPException) as exc_info:
            get_movies(page=1, page_size=1001, db=mock_db, current_user=mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Page size cannot exceed 1000" in str(exc_info.value.detail)
    
    def test_get_movies_with_complex_filters(self, mock_db, mock_user):
        """Test movie filtering with all filters applied"""
        filters = MovieFilters(
            search="Star Wars",
            viewing_status=ViewingStatus.WATCHED,
            genre="Science Fiction",
            is_favorite=True,
            min_year=1977,
            max_year=2023,
            min_runtime=100,
            max_runtime=180
        )
        
        # Mock empty result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        result = get_movies(
            page=1, 
            page_size=10, 
            filters=filters,
            db=mock_db, 
            current_user=mock_user
        )
        
        assert result["total"] == 0
        assert result["movies"] == []
        assert result["page"] == 1
        
        # Verify all filters were applied
        assert mock_query.filter.call_count >= 8  # All filter conditions
    
    def test_toggle_favorite_concurrency_issue(self, mock_db, mock_user):
        """Test toggling favorite when movie state changes between read and write"""
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Test Movie",
            is_favorite=False
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = movie
        mock_db.query.return_value = mock_query
        
        # Simulate concurrent modification
        def commit_side_effect():
            movie.is_favorite = True  # Changed by another transaction
            raise IntegrityError("concurrent update", None, None)
        
        mock_db.commit.side_effect = commit_side_effect
        
        with pytest.raises(HTTPException) as exc_info:
            toggle_favorite(str(movie.id), mock_db, mock_user)
        
        assert exc_info.value.status_code == 500
    
    @patch('app.api.movies.movie_recommendation_service')
    def test_fetch_movie_details_with_service_timeout(self, mock_service, mock_db, mock_user):
        """Test movie details fetching when external service times out"""
        mock_service.fetch_movie_details.side_effect = TimeoutError("Service timeout")
        
        request = MovieDetailsRequest(
            title="Inception",
            year=2010
        )
        
        with pytest.raises(HTTPException) as exc_info:
            fetch_movie_details(request, mock_db, mock_user)
        
        assert exc_info.value.status_code == 500
        assert "timeout" in str(exc_info.value.detail).lower()
    
    @patch('app.api.movies.movie_recommendation_service')
    def test_fetch_movie_details_no_results(self, mock_service, mock_db, mock_user):
        """Test movie details fetching when no results found"""
        mock_service.fetch_movie_details.return_value = None
        
        request = MovieDetailsRequest(
            title="Nonexistent Movie XYZ123",
            year=2099
        )
        
        with pytest.raises(HTTPException) as exc_info:
            fetch_movie_details(request, mock_db, mock_user)
        
        assert exc_info.value.status_code == 404
        assert "No movie details found" in str(exc_info.value.detail)
    
    def test_import_netflix_empty_file(self, mock_db, mock_user):
        """Test Netflix import with empty CSV file"""
        from fastapi import UploadFile
        import io
        
        # Create empty file
        empty_file = UploadFile(
            filename="netflix_history.csv",
            file=io.BytesIO(b"")
        )
        
        with patch('app.api.movies.netflix_import_service') as mock_service:
            mock_service.import_viewing_history.return_value = {
                'success': False,
                'message': 'No valid entries found in CSV',
                'imported': 0,
                'skipped': 0,
                'errors': 0
            }
            
            result = import_from_netflix(empty_file, mock_db, mock_user)
            
            assert result["success"] is False
            assert "No valid entries" in result["message"]
    
    def test_import_netflix_malformed_csv(self, mock_db, mock_user):
        """Test Netflix import with malformed CSV"""
        from fastapi import UploadFile
        import io
        
        # Create malformed CSV
        malformed_csv = b"This is not a valid CSV\nTitle:Movie\nDate:NotADate"
        malformed_file = UploadFile(
            filename="bad_netflix.csv",
            file=io.BytesIO(malformed_csv)
        )
        
        with patch('app.api.movies.netflix_import_service') as mock_service:
            mock_service.import_viewing_history.side_effect = Exception("CSV parsing error")
            
            with pytest.raises(HTTPException) as exc_info:
                import_from_netflix(malformed_file, mock_db, mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Import failed" in str(exc_info.value.detail)
    
    def test_create_movie_with_extreme_values(self, mock_db, mock_user):
        """Test movie creation with boundary values"""
        # Very long title
        extreme_movie = MovieCreate(
            title="A" * 1000,  # 1000 character title
            description="B" * 5000,  # 5000 character description
            genre="Action",
            release_year=1895,  # First movie year
            runtime=51420,  # 35.7 days in minutes
            viewing_status=ViewingStatus.WANT_TO_WATCH
        )
        
        # Should handle gracefully
        result = create_movie(extreme_movie, mock_db, mock_user)
        assert result.title == "A" * 1000
        
        # Invalid year (future)
        future_movie = MovieCreate(
            title="Future Movie",
            release_year=datetime.now().year + 100,
            viewing_status=ViewingStatus.WANT_TO_WATCH
        )
        
        # Should still create (no validation on future years)
        result = create_movie(future_movie, mock_db, mock_user)
        assert result.release_year == datetime.now().year + 100
    
    def test_get_movie_with_malformed_uuid(self, mock_db, mock_user):
        """Test getting movie with invalid UUID format"""
        with pytest.raises(HTTPException) as exc_info:
            get_movie("not-a-uuid", mock_db, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Invalid movie ID" in str(exc_info.value.detail)
        
        # SQL injection attempt
        with pytest.raises(HTTPException) as exc_info:
            get_movie("'; DROP TABLE movies; --", mock_db, mock_user)
        
        assert exc_info.value.status_code == 400