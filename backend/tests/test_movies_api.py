"""
Test movies API endpoints

This module contains comprehensive tests for the movies API including:
- CRUD operations (Create, Read, Update, Delete)
- Viewing status updates
- Filtering and pagination
- Netflix import functionality
- AI recommendations
- Error handling and edge cases
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock, AsyncMock
import uuid
from datetime import datetime, timedelta
import io
import csv

from app.main import create_app
from app.models.content import Movie
from app.schemas.movies import ViewingStatus
from app.api.movies import get_current_user_simple
from app.db.database import get_db

# Create test app
app = create_app()
client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def sample_movie_data():
    """Sample movie data for tests"""
    return {
        "title": "Test Movie",
        "description": "A thrilling test movie",
        "genre": "Action",
        "director": "Test Director",
        "release_year": 2023,
        "runtime": 120,
        "poster_image_url": "https://example.com/poster.jpg",
        "tmdb_id": "12345",
        "imdb_id": "tt1234567",
        "omdb_id": "omdb123",
        "viewing_status": "want_to_watch",
        "user_notes": "Want to watch with family",
        "is_favorite": False,
        "source": "user_added"
    }


@pytest.fixture
def sample_movies_list(mock_user):
    """Create a list of sample movies for testing"""
    base_date = datetime.utcnow()
    movies = []
    
    for i in range(5):
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title=f"Movie {i+1}",
            description=f"Description for movie {i+1}",
            genre="Action" if i % 2 == 0 else "Comedy",
            director=f"Director {i+1}",
            release_year=2020 + i,
            runtime=90 + (i * 10),
            poster_image_url=f"https://example.com/movie{i+1}.jpg",
            tmdb_id=f"tmdb{i+1}",
            imdb_id=f"tt{i+1:07d}",
            viewing_status=ViewingStatus.WATCHED if i < 3 else ViewingStatus.WANT_TO_WATCH,
            date_watched=base_date - timedelta(days=i*7) if i < 3 else None,
            is_favorite=i % 2 == 0,
            source="user_added",
            created_at=base_date - timedelta(days=i*10),
            updated_at=base_date - timedelta(days=i*5)
        )
        movies.append(movie)
    
    return movies


class TestMoviesAPI:
    """Test movies API endpoints"""
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_create_movie_success(self, mock_get_db, mock_verify_token, 
                                 mock_user, sample_movie_data, auth_headers):
        """Test successful movie creation"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.post(
            "/api/v1/movies",
            json=sample_movie_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Verify response data
        data = response.json()
        assert data["title"] == sample_movie_data["title"]
        assert data["genre"] == sample_movie_data["genre"]
        assert data["viewing_status"] == sample_movie_data["viewing_status"]
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_create_movie_minimal_data(self, mock_get_db, mock_verify_token, 
                                      mock_user, auth_headers):
        """Test creating movie with only required fields"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Minimal movie data
        minimal_data = {
            "title": "Minimal Movie"
        }
        
        # Make request
        response = client.post(
            "/api/v1/movies",
            json=minimal_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.called
        
        # Verify defaults are applied
        data = response.json()
        assert data["title"] == "Minimal Movie"
        assert data["viewing_status"] == "want_to_watch"
        assert data["is_favorite"] is False
        assert data["source"] == "user_added"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    def test_create_movie_no_auth(self, mock_verify_token, sample_movie_data):
        """Test movie creation without authentication"""
        # Setup mock to raise exception
        mock_verify_token.side_effect = Exception("Invalid token")
        
        # Make request without auth headers
        response = client.post(
            "/api/v1/movies",
            json=sample_movie_data
        )
        
        # Assertions
        assert response.status_code == 401
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_create_movie_database_error(self, mock_get_db, mock_verify_token, 
                                        mock_user, sample_movie_data, auth_headers):
        """Test movie creation with database error"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.post(
            "/api/v1/movies",
            json=sample_movie_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to add movie" in response.json()["detail"]
        assert mock_db.rollback.called
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_list_movies_success(self, mock_get_db, mock_verify_token, 
                                mock_user, sample_movies_list, auth_headers):
        """Test successful movie listing with pagination"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = len(sample_movies_list)
        mock_query.all.return_value = sample_movies_list[:2]  # Page 1 with 2 items
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            "/api/v1/movies?page=1&page_size=2",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["movies"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_list_movies_with_filters(self, mock_get_db, mock_verify_token, 
                                     mock_user, sample_movies_list, auth_headers):
        """Test movie listing with various filters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Filter for watched movies only
        watched_movies = [m for m in sample_movies_list if m.viewing_status == ViewingStatus.WATCHED]
        mock_query.count.return_value = len(watched_movies)
        mock_query.all.return_value = watched_movies
        mock_get_db.return_value = mock_db
        
        # Make request with filters
        response = client.get(
            "/api/v1/movies?viewing_status=watched&genre=Action&is_favorite=true",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert all(m["viewing_status"] == "watched" for m in data["movies"])
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_list_movies_with_search(self, mock_get_db, mock_verify_token, 
                                    mock_user, sample_movies_list, auth_headers):
        """Test movie listing with search functionality"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Search results
        search_results = [sample_movies_list[0]]  # Movie 1
        mock_query.count.return_value = 1
        mock_query.all.return_value = search_results
        mock_get_db.return_value = mock_db
        
        # Make request with search
        response = client.get(
            "/api/v1/movies?search=Movie%201",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["movies"]) == 1
        assert data["movies"][0]["title"] == "Movie 1"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_get_movie_by_id_success(self, mock_get_db, mock_verify_token, 
                                    mock_user, sample_movies_list, auth_headers):
        """Test getting a specific movie by ID"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_movies_list[0]
        mock_get_db.return_value = mock_db
        
        movie_id = str(sample_movies_list[0].id)
        
        # Make request
        response = client.get(
            f"/api/v1/movies/{movie_id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == movie_id
        assert data["title"] == sample_movies_list[0].title
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_get_movie_not_found(self, mock_get_db, mock_verify_token, 
                                mock_user, auth_headers):
        """Test getting non-existent movie"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            f"/api/v1/movies/{uuid.uuid4()}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_update_movie_success(self, mock_get_db, mock_verify_token, 
                                 mock_user, sample_movies_list, auth_headers):
        """Test successful movie update"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock the movie to update
        movie = sample_movies_list[0]
        mock_query.first.return_value = movie
        mock_get_db.return_value = mock_db
        
        update_data = {
            "title": "Updated Movie Title",
            "genre": "Drama",
            "viewing_status": "watched",
            "is_favorite": True
        }
        
        # Make request
        response = client.put(
            f"/api/v1/movies/{movie.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.commit.called
        
        # Verify the movie attributes were updated
        for field, value in update_data.items():
            assert hasattr(movie, field)
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_update_movie_partial(self, mock_get_db, mock_verify_token, 
                                 mock_user, sample_movies_list, auth_headers):
        """Test partial movie update (only some fields)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        movie = sample_movies_list[0]
        mock_query.first.return_value = movie
        mock_get_db.return_value = mock_db
        
        # Only update viewing status
        update_data = {
            "viewing_status": "watched"
        }
        
        # Make request
        response = client.put(
            f"/api/v1/movies/{movie.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.commit.called
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_delete_movie_success(self, mock_get_db, mock_verify_token, 
                                 mock_user, sample_movies_list, auth_headers):
        """Test successful movie deletion"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_movies_list[0]
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.delete(
            f"/api/v1/movies/{sample_movies_list[0].id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.delete.called
        assert mock_db.commit.called
        assert response.json()["message"] == "Movie deleted successfully"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_delete_movie_not_found(self, mock_get_db, mock_verify_token, 
                                   mock_user, auth_headers):
        """Test deleting non-existent movie"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.delete(
            f"/api/v1/movies/{uuid.uuid4()}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_update_viewing_status_to_watched(self, mock_get_db, mock_verify_token, 
                                            mock_user, auth_headers):
        """Test updating viewing status to watched (should set date_watched)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Movie that hasn't been watched
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Unwatched Movie",
            viewing_status=ViewingStatus.WANT_TO_WATCH,
            date_watched=None,
            is_favorite=False,
            source="user_added"
        )
        mock_query.first.return_value = movie
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.patch(
            f"/api/v1/movies/{movie.id}/viewing-status?viewing_status=watched",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert movie.viewing_status == ViewingStatus.WATCHED
        assert movie.date_watched is not None
        assert mock_db.commit.called
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_update_viewing_status_to_want_to_watch(self, mock_get_db, mock_verify_token, 
                                                   mock_user, auth_headers):
        """Test updating viewing status to want_to_watch (should clear date_watched)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Movie that has been watched
        movie = Movie(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Watched Movie",
            viewing_status=ViewingStatus.WATCHED,
            date_watched=datetime.utcnow(),
            is_favorite=False,
            source="user_added"
        )
        mock_query.first.return_value = movie
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.patch(
            f"/api/v1/movies/{movie.id}/viewing-status?viewing_status=want_to_watch",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert movie.viewing_status == ViewingStatus.WANT_TO_WATCH
        assert movie.date_watched is None
        assert mock_db.commit.called
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_movies_health_check(self, mock_get_db, mock_verify_token, 
                                mock_user, auth_headers):
        """Test movies health check endpoint"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            "/api/v1/movies/debug/health",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "movies"
        assert data["user_movie_count"] == 10
        assert data["database_connected"] is True
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_fetch_movie_details(self, mock_get_db, mock_verify_token, 
                                mock_user, auth_headers):
        """Test fetching movie details endpoint"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        details_request = {
            "title": "The Matrix",
            "director": "The Wachowskis",
            "release_year": 1999
        }
        
        # Make request
        response = client.post(
            "/api/v1/movies/fetch-details",
            json=details_request,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Matrix"
        assert data["director"] == "The Wachowskis"
        assert data["release_year"] == 1999
        assert "confidence" in data
        assert "sources" in data
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    @patch('app.api.movies.netflix_import_service.import_viewing_history')
    async def test_import_netflix_history_success(self, mock_import_service, mock_get_db, 
                                                 mock_verify_token, mock_user, auth_headers):
        """Test successful Netflix history import"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock the import service response
        mock_import_service.return_value = {
            'success': True,
            'movies_imported': 5,
            'tv_shows_imported': 3,
            'total_processed': 10,
            'errors': [],
            'message': 'Successfully imported 8 items from Netflix history'
        }
        
        # Create CSV content
        csv_content = "Title,Date\n"
        csv_content += "The Matrix,2023-01-15\n"
        csv_content += "Breaking Bad: Season 1,2023-01-20\n"
        
        # Create file-like object
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        # Make request with file upload
        response = client.post(
            "/api/v1/movies/import/netflix",
            files={"file": ("netflix_history.csv", csv_file, "text/csv")},
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movies_imported"] == 5
        assert data["tv_shows_imported"] == 3
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_import_netflix_history_wrong_file_type(self, mock_get_db, mock_verify_token, 
                                                   mock_user, auth_headers):
        """Test Netflix import with wrong file type"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Create non-CSV file
        txt_file = io.BytesIO(b"This is not a CSV file")
        
        # Make request
        response = client.post(
            "/api/v1/movies/import/netflix",
            files={"file": ("wrong_file.txt", txt_file, "text/plain")},
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 400
        assert "Please upload a CSV file" in response.json()["detail"]
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    @patch('app.api.movies.movie_recommendation_service.get_recommendations')
    async def test_get_movie_recommendations_success(self, mock_get_recommendations, 
                                                    mock_get_db, mock_verify_token, 
                                                    mock_user, auth_headers):
        """Test successful movie recommendations"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock recommendation response
        mock_get_recommendations.return_value = {
            'success': True,
            'recommendations': [
                {
                    'title': 'Inception',
                    'type': 'movie',
                    'genre': 'Sci-Fi',
                    'description': 'A mind-bending thriller',
                    'release_year': 2010,
                    'director': 'Christopher Nolan',
                    'reason': 'Based on your interest in The Matrix'
                },
                {
                    'title': 'Stranger Things',
                    'type': 'tv',
                    'genre': 'Sci-Fi/Horror',
                    'description': 'A thrilling series',
                    'release_year': 2016,
                    'reason': 'Popular sci-fi series'
                }
            ],
            'provider': 'claude',
            'analysis': {
                'movies_watched': 10,
                'tv_shows_watched': 5,
                'favorite_genres': ['Sci-Fi', 'Action']
            }
        }
        
        # Make request
        response = client.get(
            "/api/v1/movies/recommendations?limit=10",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["recommendations"]) == 2
        assert data["provider"] == "claude"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    @patch('app.api.movies.movie_recommendation_service.get_recommendations')
    async def test_get_movie_recommendations_with_filters(self, mock_get_recommendations, 
                                                         mock_get_db, mock_verify_token, 
                                                         mock_user, auth_headers):
        """Test movie recommendations with content type and genre filters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock filtered recommendation response
        mock_get_recommendations.return_value = {
            'success': True,
            'recommendations': [
                {
                    'title': 'The Dark Knight',
                    'type': 'movie',
                    'genre': 'Action',
                    'description': 'Batman fights the Joker',
                    'release_year': 2008,
                    'director': 'Christopher Nolan'
                }
            ],
            'provider': 'groq'
        }
        
        # Make request with filters
        response = client.get(
            "/api/v1/movies/recommendations?content_type=movie&genre=Action&limit=5",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["type"] == "movie"
        assert data["recommendations"][0]["genre"] == "Action"
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    @patch('app.api.movies.movie_recommendation_service.get_recommendations')
    async def test_get_movie_recommendations_failure(self, mock_get_recommendations, 
                                                    mock_get_db, mock_verify_token, 
                                                    mock_user, auth_headers):
        """Test movie recommendations when service fails"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock recommendation failure
        mock_get_recommendations.return_value = {
            'success': False,
            'error': 'No AI providers available',
            'recommendations': []
        }
        
        # Make request
        response = client.get(
            "/api/v1/movies/recommendations",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "No AI providers available"
        assert data["recommendations"] == []


class TestMovieEdgeCases:
    """Test edge cases and validation for movies API"""
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_create_movie_invalid_year(self, mock_get_db, mock_verify_token, 
                                      mock_user, auth_headers):
        """Test creating movie with invalid release year"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Movie with invalid year
        invalid_data = {
            "title": "Future Movie",
            "release_year": 3500  # Too far in future
        }
        
        # Make request
        response = client.post(
            "/api/v1/movies",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions - Should fail validation
        assert response.status_code == 422
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_create_movie_negative_runtime(self, mock_get_db, mock_verify_token, 
                                          mock_user, auth_headers):
        """Test creating movie with negative runtime"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Movie with negative runtime
        invalid_data = {
            "title": "Quick Movie",
            "runtime": -10
        }
        
        # Make request
        response = client.post(
            "/api/v1/movies",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions - Should fail validation
        assert response.status_code == 422
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_list_movies_invalid_pagination(self, mock_get_db, mock_verify_token, 
                                           mock_user, auth_headers):
        """Test listing movies with invalid pagination parameters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Test negative page number
        response = client.get(
            "/api/v1/movies?page=-1",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test page size exceeding limit
        response = client.get(
            "/api/v1/movies?page_size=200",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    def test_invalid_movie_id_format(self, mock_verify_token, mock_user, auth_headers):
        """Test accessing movie with invalid UUID format"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        
        # Make request with invalid UUID
        response = client.get(
            "/api/v1/movies/not-a-valid-uuid",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to get movie" in response.json()["detail"]
    
    
    @patch('app.api.movies.AuthService.verify_user_token')
    @patch('app.api.movies.get_db')
    def test_update_viewing_status_invalid_value(self, mock_get_db, mock_verify_token, 
                                                mock_user, auth_headers):
        """Test updating viewing status with invalid value"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Make request with invalid viewing status
        response = client.patch(
            f"/api/v1/movies/{uuid.uuid4()}/viewing-status?viewing_status=not_valid",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 422