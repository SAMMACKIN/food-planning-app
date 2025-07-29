"""
Test TV Shows API endpoints

This module contains comprehensive tests for the TV shows API including:
- CRUD operations (Create, Read, Update, Delete)
- Viewing status updates
- Episode tracking functionality
- Bulk episode operations
- Progress tracking
- Filtering and pagination
- Health check endpoint
- TV show details fetching
- Error handling and edge cases
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock, AsyncMock
import uuid
from datetime import datetime, timedelta
import io
import json

from app.main import create_app
from app.models.content import TVShow, EpisodeWatch
from app.schemas.tv_shows import ViewingStatus, ShowStatus
from app.api.tv_shows import get_current_user_simple
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
def sample_tv_show_data():
    """Sample TV show data for tests"""
    return {
        "title": "Test TV Show",
        "description": "A thrilling test TV series",
        "genre": "Drama",
        "network": "Test Network",
        "total_seasons": 5,
        "total_episodes": 50,
        "status": "running",
        "first_air_date": "2023-01-15T00:00:00",
        "last_air_date": None,
        "poster_image_url": "https://example.com/tvshow_poster.jpg",
        "tmdb_id": "12345",
        "tvmaze_id": "67890",
        "imdb_id": "tt1234567",
        "viewing_status": "want_to_watch",
        "current_season": 1,
        "current_episode": 1,
        "episodes_watched": 0,
        "user_notes": "Want to watch with family",
        "is_favorite": False,
        "source": "user_added"
    }


@pytest.fixture
def sample_tv_shows_list(mock_user):
    """Create a list of sample TV shows for testing"""
    base_date = datetime.utcnow()
    tv_shows = []
    
    for i in range(5):
        tv_show = TVShow(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title=f"TV Show {i+1}",
            description=f"Description for TV show {i+1}",
            genre="Drama" if i % 2 == 0 else "Comedy",
            network=f"Network {i+1}",
            total_seasons=3 + i,
            total_episodes=30 + (i * 10),
            status="running" if i < 3 else "ended",
            first_air_date=base_date - timedelta(days=365*(5-i)),
            last_air_date=None if i < 3 else base_date - timedelta(days=30*i),
            poster_image_url=f"https://example.com/show{i+1}.jpg",
            tmdb_id=f"tmdb{i+1}",
            tvmaze_id=f"tvmaze{i+1}",
            imdb_id=f"tt{i+1:07d}",
            viewing_status=ViewingStatus.WATCHING if i < 2 else ViewingStatus.COMPLETED if i < 4 else ViewingStatus.WANT_TO_WATCH,
            current_season=2 if i < 2 else 1,
            current_episode=5 if i < 2 else 1,
            episodes_watched=15 if i < 2 else 30 + (i * 10) if i < 4 else 0,
            date_started=base_date - timedelta(days=i*30) if i < 4 else None,
            date_finished=base_date - timedelta(days=i*7) if 2 <= i < 4 else None,
            is_favorite=i % 2 == 0,
            source="user_added",
            created_at=base_date - timedelta(days=i*60),
            updated_at=base_date - timedelta(days=i*5)
        )
        tv_shows.append(tv_show)
    
    return tv_shows


@pytest.fixture
def sample_episode_data():
    """Sample episode data for tests"""
    return {
        "season_number": 1,
        "episode_number": 5,
        "episode_title": "Test Episode",
        "watched": True,
        "watch_date": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_episodes_list(mock_user, sample_tv_shows_list):
    """Create a list of sample episodes for testing"""
    base_date = datetime.utcnow()
    episodes = []
    tv_show_id = sample_tv_shows_list[0].id
    
    # Create episodes for first 2 seasons
    for season in range(1, 3):
        for episode in range(1, 11):
            episode_watch = EpisodeWatch(
                id=uuid.uuid4(),
                tv_show_id=tv_show_id,
                user_id=uuid.UUID(mock_user["id"]),
                season_number=season,
                episode_number=episode,
                episode_title=f"S{season}E{episode}: Episode Title",
                watched=True if season == 1 or (season == 2 and episode <= 5) else False,
                watch_date=base_date - timedelta(days=(season-1)*30 + episode) if season == 1 or (season == 2 and episode <= 5) else None,
                created_at=base_date - timedelta(days=60),
                updated_at=base_date - timedelta(days=30)
            )
            episodes.append(episode_watch)
    
    return episodes


class TestTVShowsAPI:
    """Test TV shows API endpoints"""
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_create_tv_show_success(self, mock_get_db, mock_verify_token, 
                                   mock_user, sample_tv_show_data, auth_headers):
        """Test successful TV show creation"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=sample_tv_show_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Verify response data
        data = response.json()
        assert data["title"] == sample_tv_show_data["title"]
        assert data["genre"] == sample_tv_show_data["genre"]
        assert data["network"] == sample_tv_show_data["network"]
        assert data["total_seasons"] == sample_tv_show_data["total_seasons"]
        assert data["viewing_status"] == sample_tv_show_data["viewing_status"]
        assert data["episodes_watched"] == 0
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_create_tv_show_minimal_data(self, mock_get_db, mock_verify_token, 
                                        mock_user, auth_headers):
        """Test creating TV show with only required fields"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Minimal TV show data
        minimal_data = {
            "title": "Minimal TV Show"
        }
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=minimal_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.called
        
        # Verify defaults are applied
        data = response.json()
        assert data["title"] == "Minimal TV Show"
        assert data["viewing_status"] == "want_to_watch"
        assert data["current_season"] == 1
        assert data["current_episode"] == 1
        assert data["episodes_watched"] == 0
        assert data["is_favorite"] is False
        assert data["source"] == "user_added"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    def test_create_tv_show_no_auth(self, mock_verify_token, sample_tv_show_data):
        """Test TV show creation without authentication"""
        # Setup mock to raise exception
        mock_verify_token.side_effect = Exception("Invalid token")
        
        # Make request without auth headers
        response = client.post(
            "/api/v1/tv-shows",
            json=sample_tv_show_data
        )
        
        # Assertions
        assert response.status_code == 401
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_create_tv_show_database_error(self, mock_get_db, mock_verify_token, 
                                          mock_user, sample_tv_show_data, auth_headers):
        """Test TV show creation with database error"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=sample_tv_show_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to add TV show" in response.json()["detail"]
        assert mock_db.rollback.called
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_list_tv_shows_success(self, mock_get_db, mock_verify_token, 
                                  mock_user, sample_tv_shows_list, auth_headers):
        """Test successful TV show listing with pagination"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = len(sample_tv_shows_list)
        mock_query.all.return_value = sample_tv_shows_list[:2]  # Page 1 with 2 items
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            "/api/v1/tv-shows?page=1&page_size=2",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["tv_shows"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_list_tv_shows_with_filters(self, mock_get_db, mock_verify_token, 
                                       mock_user, sample_tv_shows_list, auth_headers):
        """Test TV show listing with various filters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Filter for watching shows only
        watching_shows = [s for s in sample_tv_shows_list if s.viewing_status == ViewingStatus.WATCHING]
        mock_query.count.return_value = len(watching_shows)
        mock_query.all.return_value = watching_shows
        mock_get_db.return_value = mock_db
        
        # Make request with filters
        response = client.get(
            "/api/v1/tv-shows?viewing_status=watching&genre=Drama&network=Network%201&is_favorite=true",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert all(s["viewing_status"] == "watching" for s in data["tv_shows"])
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_list_tv_shows_with_search(self, mock_get_db, mock_verify_token, 
                                      mock_user, sample_tv_shows_list, auth_headers):
        """Test TV show listing with search functionality"""
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
        search_results = [sample_tv_shows_list[0]]  # TV Show 1
        mock_query.count.return_value = 1
        mock_query.all.return_value = search_results
        mock_get_db.return_value = mock_db
        
        # Make request with search
        response = client.get(
            "/api/v1/tv-shows?search=TV%20Show%201",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["tv_shows"]) == 1
        assert data["tv_shows"][0]["title"] == "TV Show 1"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_get_tv_show_by_id_success(self, mock_get_db, mock_verify_token, 
                                      mock_user, sample_tv_shows_list, auth_headers):
        """Test getting a specific TV show by ID"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_tv_shows_list[0]
        mock_get_db.return_value = mock_db
        
        tv_show_id = str(sample_tv_shows_list[0].id)
        
        # Make request
        response = client.get(
            f"/api/v1/tv-shows/{tv_show_id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tv_show_id
        assert data["title"] == sample_tv_shows_list[0].title
        assert data["total_seasons"] == sample_tv_shows_list[0].total_seasons
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_get_tv_show_not_found(self, mock_get_db, mock_verify_token, 
                                  mock_user, auth_headers):
        """Test getting non-existent TV show"""
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
            f"/api/v1/tv-shows/{uuid.uuid4()}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "TV show not found"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_tv_show_success(self, mock_get_db, mock_verify_token, 
                                   mock_user, sample_tv_shows_list, auth_headers):
        """Test successful TV show update"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock the TV show to update
        tv_show = sample_tv_shows_list[0]
        mock_query.first.return_value = tv_show
        mock_get_db.return_value = mock_db
        
        update_data = {
            "title": "Updated TV Show Title",
            "genre": "Thriller",
            "viewing_status": "watching",
            "current_season": 2,
            "current_episode": 3,
            "is_favorite": True
        }
        
        # Make request
        response = client.put(
            f"/api/v1/tv-shows/{tv_show.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.commit.called
        
        # Verify the TV show attributes were updated
        for field, value in update_data.items():
            assert hasattr(tv_show, field)
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_tv_show_partial(self, mock_get_db, mock_verify_token, 
                                   mock_user, sample_tv_shows_list, auth_headers):
        """Test partial TV show update (only some fields)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        tv_show = sample_tv_shows_list[0]
        mock_query.first.return_value = tv_show
        mock_get_db.return_value = mock_db
        
        # Only update viewing status and current episode
        update_data = {
            "viewing_status": "watching",
            "current_episode": 6
        }
        
        # Make request
        response = client.put(
            f"/api/v1/tv-shows/{tv_show.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.commit.called
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_delete_tv_show_success(self, mock_get_db, mock_verify_token, 
                                   mock_user, sample_tv_shows_list, auth_headers):
        """Test successful TV show deletion"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_tv_shows_list[0]
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.delete(
            f"/api/v1/tv-shows/{sample_tv_shows_list[0].id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.delete.called
        assert mock_db.commit.called
        assert response.json()["message"] == "TV show deleted successfully"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_delete_tv_show_not_found(self, mock_get_db, mock_verify_token, 
                                     mock_user, auth_headers):
        """Test deleting non-existent TV show"""
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
            f"/api/v1/tv-shows/{uuid.uuid4()}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "TV show not found"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_viewing_status_to_watching(self, mock_get_db, mock_verify_token, 
                                             mock_user, auth_headers):
        """Test updating viewing status to watching (should set date_started)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # TV show that hasn't been started
        tv_show = TVShow(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Unwatched Show",
            viewing_status=ViewingStatus.WANT_TO_WATCH,
            date_started=None,
            date_finished=None,
            current_season=1,
            current_episode=1,
            episodes_watched=0,
            is_favorite=False,
            source="user_added"
        )
        mock_query.first.return_value = tv_show
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.patch(
            f"/api/v1/tv-shows/{tv_show.id}/viewing-status?viewing_status=watching",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert tv_show.viewing_status == ViewingStatus.WATCHING
        assert tv_show.date_started is not None
        assert tv_show.date_finished is None
        assert mock_db.commit.called
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_viewing_status_to_completed(self, mock_get_db, mock_verify_token, 
                                              mock_user, auth_headers):
        """Test updating viewing status to completed (should set date_finished)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # TV show that is being watched
        tv_show = TVShow(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Watching Show",
            viewing_status=ViewingStatus.WATCHING,
            date_started=datetime.utcnow() - timedelta(days=30),
            date_finished=None,
            current_season=3,
            current_episode=10,
            episodes_watched=30,
            is_favorite=True,
            source="user_added"
        )
        mock_query.first.return_value = tv_show
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.patch(
            f"/api/v1/tv-shows/{tv_show.id}/viewing-status?viewing_status=completed",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert tv_show.viewing_status == ViewingStatus.COMPLETED
        assert tv_show.date_finished is not None
        assert mock_db.commit.called
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_viewing_status_to_want_to_watch(self, mock_get_db, mock_verify_token, 
                                                   mock_user, auth_headers):
        """Test updating viewing status to want_to_watch (should clear dates)"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # TV show that has been completed
        tv_show = TVShow(
            id=uuid.uuid4(),
            user_id=uuid.UUID(mock_user["id"]),
            title="Completed Show",
            viewing_status=ViewingStatus.COMPLETED,
            date_started=datetime.utcnow() - timedelta(days=60),
            date_finished=datetime.utcnow() - timedelta(days=7),
            current_season=5,
            current_episode=1,
            episodes_watched=50,
            is_favorite=True,
            source="user_added"
        )
        mock_query.first.return_value = tv_show
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.patch(
            f"/api/v1/tv-shows/{tv_show.id}/viewing-status?viewing_status=want_to_watch",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert tv_show.viewing_status == ViewingStatus.WANT_TO_WATCH
        assert tv_show.date_started is None
        assert tv_show.date_finished is None
        assert mock_db.commit.called


class TestEpisodeTracking:
    """Test episode tracking functionality"""
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_get_episodes_success(self, mock_get_db, mock_verify_token, 
                                 mock_user, sample_tv_shows_list, sample_episodes_list, auth_headers):
        """Test getting episodes for a TV show"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        mock_query.first.return_value = tv_show
        
        # Mock episode query
        mock_query.all.return_value = sample_episodes_list[:10]  # First 10 episodes
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            f"/api/v1/tv-shows/{tv_show.id}/episodes",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["episodes"]) == 10
        assert data["total"] == 10
        assert all("season_number" in ep and "episode_number" in ep for ep in data["episodes"])
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_get_episodes_with_filters(self, mock_get_db, mock_verify_token, 
                                      mock_user, sample_tv_shows_list, sample_episodes_list, auth_headers):
        """Test getting episodes with season and watched filters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        mock_query.first.return_value = tv_show
        
        # Filter for season 1 watched episodes only
        season1_watched = [ep for ep in sample_episodes_list if ep.season_number == 1 and ep.watched]
        mock_query.all.return_value = season1_watched
        mock_get_db.return_value = mock_db
        
        # Make request with filters
        response = client.get(
            f"/api/v1/tv-shows/{tv_show.id}/episodes?season=1&watched=true",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert all(ep["season_number"] == 1 and ep["watched"] is True for ep in data["episodes"])
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_mark_episode_watched_new(self, mock_get_db, mock_verify_token, 
                                     mock_user, sample_tv_shows_list, auth_headers):
        """Test marking a new episode as watched"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        mock_query.first.side_effect = [tv_show, None]  # TV show exists, episode doesn't
        
        # Mock episode count queries
        mock_query.count.return_value = 16  # Total watched episodes after marking
        
        # Mock latest watched episode query
        latest_episode = MagicMock()
        latest_episode.season_number = 2
        latest_episode.episode_number = 6
        mock_query.order_by.return_value.first.return_value = latest_episode
        
        mock_get_db.return_value = mock_db
        
        episode_data = {
            "season_number": 2,
            "episode_number": 6,
            "episode_title": "New Episode",
            "watched": True
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{tv_show.id}/episodes",
            json=episode_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.called
        assert mock_db.commit.called
        
        data = response.json()
        assert data["season_number"] == 2
        assert data["episode_number"] == 6
        assert data["watched"] is True
        assert data["watch_date"] is not None
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_mark_episode_watched_existing(self, mock_get_db, mock_verify_token, 
                                          mock_user, sample_tv_shows_list, sample_episodes_list, auth_headers):
        """Test updating existing episode watch status"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        existing_episode = sample_episodes_list[14]  # S2E5 - currently watched
        existing_episode.watched = True
        
        mock_query.first.side_effect = [tv_show, existing_episode]
        
        # Mock episode count queries
        mock_query.count.return_value = 14  # Total watched episodes after unmarking
        
        mock_get_db.return_value = mock_db
        
        episode_data = {
            "season_number": 2,
            "episode_number": 5,
            "watched": False  # Unmark as watched
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{tv_show.id}/episodes",
            json=episode_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.commit.called
        assert existing_episode.watched is False
        assert existing_episode.watch_date is None
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_get_watch_progress(self, mock_get_db, mock_verify_token, 
                               mock_user, sample_tv_shows_list, sample_episodes_list, auth_headers):
        """Test getting watch progress for a TV show"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock TV show
        tv_show = sample_tv_shows_list[0]
        tv_show.episodes_watched = 15
        tv_show.total_episodes = 50
        mock_query.first.return_value = tv_show
        
        # Mock last watched episode
        last_watched = sample_episodes_list[14]  # S2E5
        mock_query.order_by.return_value.first.return_value = last_watched
        
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            f"/api/v1/tv-shows/{tv_show.id}/progress",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["tv_show_id"] == str(tv_show.id)
        assert data["tv_show_title"] == tv_show.title
        assert data["current_season"] == tv_show.current_season
        assert data["current_episode"] == tv_show.current_episode
        assert data["episodes_watched"] == 15
        assert data["total_episodes"] == 50
        assert data["completion_percentage"] == 30.0  # 15/50 * 100
        assert data["viewing_status"] == tv_show.viewing_status
        assert data["last_watched_date"] is not None
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    @patch('app.api.tv_shows.mark_episode')
    def test_update_progress(self, mock_mark_episode, mock_get_db, mock_verify_token, 
                            mock_user, auth_headers):
        """Test updating progress by marking an episode"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock mark_episode response
        mock_episode_response = MagicMock()
        mock_mark_episode.return_value = mock_episode_response
        
        progress_data = {
            "season_number": 2,
            "episode_number": 7,
            "mark_watched": True
        }
        
        # Make request
        response = client.patch(
            f"/api/v1/tv-shows/{uuid.uuid4()}/progress",
            json=progress_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_mark_episode.called
        
        data = response.json()
        assert data["message"] == "Progress updated successfully"
        assert data["season"] == 2
        assert data["episode_number"] == 7
        assert data["watched"] is True
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_bulk_mark_episodes(self, mock_get_db, mock_verify_token, 
                               mock_user, sample_tv_shows_list, auth_headers):
        """Test bulk marking episodes as watched/unwatched"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        mock_query.first.side_effect = [tv_show] + [None] * 5  # TV show exists, episodes don't
        
        # Mock episode count after update
        mock_query.count.return_value = 20
        
        mock_get_db.return_value = mock_db
        
        bulk_data = {
            "season_number": 3,
            "episodes": [1, 2, 3, 4, 5],
            "watched": True
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{tv_show.id}/episodes/bulk",
            json=bulk_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.call_count == 5  # 5 new episodes added
        assert mock_db.commit.called
        
        data = response.json()
        assert data["message"] == "Marked 5 episodes as watched"
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_bulk_mark_episodes_mixed_existing(self, mock_get_db, mock_verify_token, 
                                              mock_user, sample_tv_shows_list, sample_episodes_list, auth_headers):
        """Test bulk marking with some existing episodes"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock TV show verification
        tv_show = sample_tv_shows_list[0]
        existing_episode1 = sample_episodes_list[0]  # S1E1
        existing_episode2 = sample_episodes_list[1]  # S1E2
        
        # Some episodes exist, some don't
        mock_query.first.side_effect = [tv_show, existing_episode1, existing_episode2, None, None, None]
        
        # Mock episode count after update
        mock_query.count.return_value = 15
        
        mock_get_db.return_value = mock_db
        
        bulk_data = {
            "season_number": 1,
            "episodes": [1, 2, 3, 4, 5],
            "watched": False  # Unmark as watched
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{tv_show.id}/episodes/bulk",
            json=bulk_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        assert mock_db.add.call_count == 3  # 3 new episodes added
        assert mock_db.commit.called
        assert existing_episode1.watched is False
        assert existing_episode2.watched is False
        
        data = response.json()
        assert data["message"] == "Marked 5 episodes as unwatched"


class TestTVShowsHealthAndDetails:
    """Test health check and details fetching endpoints"""
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_tv_shows_health_check(self, mock_get_db, mock_verify_token, 
                                  mock_user, auth_headers):
        """Test TV shows health check endpoint"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [15, 150]  # 15 TV shows, 150 episodes
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            "/api/v1/tv-shows/debug/health",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "tv_shows"
        assert data["user_tv_show_count"] == 15
        assert data["user_episode_count"] == 150
        assert data["database_connected"] is True
        assert data["table_accessible"] is True
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_tv_shows_health_check_error(self, mock_get_db, mock_verify_token, 
                                        mock_user, auth_headers):
        """Test TV shows health check with database error"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = Exception("Database connection error")
        mock_get_db.return_value = mock_db
        
        # Make request
        response = client.get(
            "/api/v1/tv-shows/debug/health",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200  # Health check returns 200 even on error
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["service"] == "tv_shows"
        assert "error" in data
        assert data["database_connected"] is False
        assert data["table_accessible"] is False
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    async def test_fetch_tv_show_details(self, mock_get_db, mock_verify_token, 
                                        mock_user, auth_headers):
        """Test fetching TV show details endpoint"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        details_request = {
            "title": "Breaking Bad",
            "network": "AMC",
            "first_air_year": 2008
        }
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows/fetch-details",
            json=details_request,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Breaking Bad"
        assert data["network"] == "AMC"
        assert "confidence" in data
        assert "sources" in data
        assert data["confidence"] == 0.5  # Default confidence for now
        assert "manual_entry" in data["sources"]


class TestTVShowEdgeCases:
    """Test edge cases and validation for TV shows API"""
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_create_tv_show_invalid_seasons(self, mock_get_db, mock_verify_token, 
                                           mock_user, auth_headers):
        """Test creating TV show with invalid season count"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # TV show with negative seasons
        invalid_data = {
            "title": "Invalid Show",
            "total_seasons": -1
        }
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions - Should fail validation
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_create_tv_show_invalid_episodes(self, mock_get_db, mock_verify_token, 
                                            mock_user, auth_headers):
        """Test creating TV show with negative episode count"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # TV show with negative episodes
        invalid_data = {
            "title": "Quick Show",
            "total_episodes": -10
        }
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions - Should fail validation
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_list_tv_shows_invalid_pagination(self, mock_get_db, mock_verify_token, 
                                             mock_user, auth_headers):
        """Test listing TV shows with invalid pagination parameters"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Test negative page number
        response = client.get(
            "/api/v1/tv-shows?page=-1",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test page size exceeding limit
        response = client.get(
            "/api/v1/tv-shows?page_size=200",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    def test_invalid_tv_show_id_format(self, mock_verify_token, mock_user, auth_headers):
        """Test accessing TV show with invalid UUID format"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        
        # Make request with invalid UUID
        response = client.get(
            "/api/v1/tv-shows/not-a-valid-uuid",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to get TV show" in response.json()["detail"]
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_update_viewing_status_invalid_value(self, mock_get_db, mock_verify_token, 
                                                mock_user, auth_headers):
        """Test updating viewing status with invalid value"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Make request with invalid viewing status
        response = client.patch(
            f"/api/v1/tv-shows/{uuid.uuid4()}/viewing-status?viewing_status=not_valid",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_mark_episode_invalid_season(self, mock_get_db, mock_verify_token, 
                                        mock_user, auth_headers):
        """Test marking episode with invalid season number"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Episode with invalid season
        invalid_data = {
            "season_number": 0,  # Should be >= 1
            "episode_number": 1,
            "watched": True
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{uuid.uuid4()}/episodes",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_mark_episode_invalid_episode(self, mock_get_db, mock_verify_token, 
                                         mock_user, auth_headers):
        """Test marking episode with invalid episode number"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Episode with invalid episode number
        invalid_data = {
            "season_number": 1,
            "episode_number": -1,  # Should be >= 1
            "watched": True
        }
        
        # Make request
        response = client.post(
            f"/api/v1/tv-shows/{uuid.uuid4()}/episodes",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_current_season_episode_validation(self, mock_get_db, mock_verify_token, 
                                              mock_user, auth_headers):
        """Test validation of current_season and current_episode fields"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Invalid current season (< 1)
        invalid_data = {
            "title": "Test Show",
            "current_season": 0
        }
        
        response = client.post(
            "/api/v1/tv-shows",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid current episode (< 1)
        invalid_data = {
            "title": "Test Show",
            "current_episode": 0
        }
        
        response = client.post(
            "/api/v1/tv-shows",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    
    @patch('app.api.tv_shows.AuthService.verify_user_token')
    @patch('app.api.tv_shows.get_db')
    def test_episodes_watched_negative(self, mock_get_db, mock_verify_token, 
                                      mock_user, auth_headers):
        """Test creating TV show with negative episodes watched"""
        # Setup mocks
        mock_verify_token.return_value = mock_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Negative episodes watched
        invalid_data = {
            "title": "Test Show",
            "episodes_watched": -5
        }
        
        # Make request
        response = client.post(
            "/api/v1/tv-shows",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 422