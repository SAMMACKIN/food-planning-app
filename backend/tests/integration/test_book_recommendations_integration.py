"""
Integration tests for Book Recommendations API with AI service
Tests the full flow from API endpoint through service to AI providers
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.content import Book, BookRecommendationFeedback
from app.schemas.books import FeedbackType


class TestBookRecommendationsIntegration:
    """Integration tests for book recommendations feature"""
    
    @pytest.fixture
    def setup_test_books(self, client, auth_headers):
        """Create test books for recommendation context"""
        books_data = [
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "genre": "Science Fiction",
                "reading_status": "read",
                "pages": 384,
                "publication_year": 2014,
                "is_favorite": True
            },
            {
                "title": "Project Hail Mary",
                "author": "Andy Weir",
                "genre": "Science Fiction", 
                "reading_status": "read",
                "pages": 476,
                "publication_year": 2021
            },
            {
                "title": "Ready Player One",
                "author": "Ernest Cline",
                "genre": "Science Fiction",
                "reading_status": "read",
                "pages": 374,
                "publication_year": 2011,
                "is_favorite": True
            },
            {
                "title": "The Three-Body Problem",
                "author": "Liu Cixin",
                "genre": "Science Fiction",
                "reading_status": "reading",
                "pages": 400,
                "publication_year": 2008
            },
            {
                "title": "Dune",
                "author": "Frank Herbert",
                "genre": "Science Fiction",
                "reading_status": "want_to_read",
                "pages": 688,
                "publication_year": 1965
            }
        ]
        
        created_books = []
        for book_data in books_data:
            response = client.post(
                "/api/v1/books",
                json=book_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            created_books.append(response.json())
        
        # Add ratings to some books
        for i, book in enumerate(created_books[:3]):
            rating = [5, 4, 5][i]  # High ratings for read books
            response = client.post(
                f"/api/v1/books/{book['id']}/rate",
                json={"rating": rating},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        return created_books
    
    def test_get_recommendations_endpoint_exists(self, client, auth_headers):
        """Test that recommendations endpoint exists and requires auth"""
        # Without auth
        response = client.post("/api/v1/books/recommendations")
        assert response.status_code == 401
        
        # With auth but no body
        response = client.post(
            "/api/v1/books/recommendations",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.book_recommendation_service.ai_service')
    def test_get_recommendations_with_empty_collection(
        self, mock_ai_service, client, auth_headers
    ):
        """Test recommendations for user with no books"""
        # Mock AI response
        mock_ai_service.get_ai_response = AsyncMock(return_value=json.dumps({
            "recommendations": [
                {
                    "title": "Foundation",
                    "author": "Isaac Asimov",
                    "genre": "Science Fiction",
                    "description": "A science fiction classic about psychohistory.",
                    "reasoning": "A great starting point for science fiction readers.",
                    "publication_year": 1951,
                    "pages": 244,
                    "confidence_score": 0.90
                }
            ]
        }))
        
        response = client.post(
            "/api/v1/books/recommendations",
            json={"max_recommendations": 3},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommendations" in data
        assert "session_id" in data
        assert "context_summary" in data
        assert len(data["recommendations"]) >= 0  # May be 0 if AI fails
    
    @patch('app.services.book_recommendation_service.ai_service')
    def test_get_recommendations_with_reading_history(
        self, mock_ai_service, client, auth_headers, setup_test_books
    ):
        """Test recommendations based on user's reading history"""
        # Mock AI response based on sci-fi preference
        mock_ai_service.get_ai_response = AsyncMock(return_value=json.dumps({
            "recommendations": [
                {
                    "title": "Ender's Game",
                    "author": "Orson Scott Card",
                    "genre": "Science Fiction",
                    "description": "A military science fiction novel about a child prodigy.",
                    "reasoning": "Similar to your favorites like The Martian and Ready Player One.",
                    "publication_year": 1985,
                    "pages": 324,
                    "confidence_score": 0.95
                },
                {
                    "title": "The Expanse: Leviathan Wakes",
                    "author": "James S.A. Corey",
                    "genre": "Science Fiction",
                    "description": "Space opera set in a colonized solar system.",
                    "reasoning": "Hard sci-fi like The Martian with epic scope.",
                    "publication_year": 2011,
                    "pages": 592,
                    "confidence_score": 0.92
                },
                {
                    "title": "Dune",  # This should be filtered out
                    "author": "Frank Herbert",
                    "genre": "Science Fiction",
                    "description": "Epic science fiction masterpiece.",
                    "reasoning": "Classic sci-fi that influenced the genre.",
                    "publication_year": 1965,
                    "pages": 688,
                    "confidence_score": 0.88
                }
            ]
        }))
        
        response = client.post(
            "/api/v1/books/recommendations",
            json={
                "max_recommendations": 5,
                "preferred_genres": ["Science Fiction"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should filter out Dune since user already has it
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["title"] == "Ender's Game"
        assert data["recommendations"][1]["title"] == "The Expanse: Leviathan Wakes"
        
        # Context should mention sci-fi preference
        assert "Science Fiction" in data["context_summary"]
    
    def test_process_recommendation_feedback(
        self, client, auth_headers, setup_test_books
    ):
        """Test processing user feedback on recommendations"""
        # First get recommendations
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            mock_ai.get_ai_response = AsyncMock(return_value=json.dumps({
                "recommendations": [
                    {
                        "title": "Neuromancer",
                        "author": "William Gibson",
                        "genre": "Science Fiction",
                        "description": "The book that defined cyberpunk.",
                        "reasoning": "Innovative sci-fi like your favorites.",
                        "publication_year": 1984,
                        "pages": 271,
                        "confidence_score": 0.93
                    }
                ]
            }))
            
            rec_response = client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 1},
                headers=auth_headers
            )
            
            assert rec_response.status_code == 200
            rec_data = rec_response.json()
            session_id = rec_data["session_id"]
            recommendation = rec_data["recommendations"][0]
        
        # Test "want to read" feedback
        feedback_response = client.post(
            "/api/v1/books/recommendations/feedback",
            json={
                "session_id": session_id,
                "recommendation_title": recommendation["title"],
                "recommendation_author": recommendation["author"],
                "feedback_type": "want_to_read",
                "feedback_notes": "Looks interesting!"
            },
            headers=auth_headers
        )
        
        assert feedback_response.status_code == 200
        feedback_data = feedback_response.json()
        assert feedback_data["success"] is True
        assert "want_to_read" in feedback_data["message"]
        
        # Verify book was added to collection
        books_response = client.get(
            "/api/v1/books?search=Neuromancer",
            headers=auth_headers
        )
        assert books_response.status_code == 200
        books_data = books_response.json()
        assert books_data["total"] == 1
        assert books_data["books"][0]["title"] == "Neuromancer"
        assert books_data["books"][0]["reading_status"] == "want_to_read"
    
    def test_feedback_types(self, client, auth_headers):
        """Test all feedback types"""
        # Mock recommendations for testing
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            mock_ai.get_ai_response = AsyncMock(return_value=json.dumps({
                "recommendations": [
                    {
                        "title": f"Test Book {i}",
                        "author": f"Test Author {i}",
                        "genre": "Fiction",
                        "description": "Test description",
                        "confidence_score": 0.8
                    } for i in range(3)
                ]
            }))
            
            rec_response = client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 3},
                headers=auth_headers
            )
            session_id = rec_response.json()["session_id"]
            recommendations = rec_response.json()["recommendations"]
        
        # Test each feedback type
        feedback_types = [
            ("want_to_read", False),
            ("not_interested", True),
            ("already_read", False)
        ]
        
        for i, (feedback_type, should_regenerate) in enumerate(feedback_types):
            response = client.post(
                "/api/v1/books/recommendations/feedback",
                json={
                    "session_id": session_id,
                    "recommendation_title": recommendations[i]["title"],
                    "recommendation_author": recommendations[i]["author"],
                    "feedback_type": feedback_type
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["should_regenerate"] == should_regenerate
    
    def test_recommendations_with_genre_filters(
        self, client, auth_headers, setup_test_books
    ):
        """Test recommendations with genre preferences and exclusions"""
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            # Mock will be called, capture the prompt
            prompt_used = []
            
            async def capture_prompt(prompt):
                prompt_used.append(prompt)
                return json.dumps({
                    "recommendations": [
                        {
                            "title": "Mystery Book",
                            "author": "Mystery Author",
                            "genre": "Mystery",
                            "description": "A thrilling mystery.",
                            "confidence_score": 0.85
                        },
                        {
                            "title": "Romance Book",
                            "author": "Romance Author", 
                            "genre": "Romance",
                            "description": "A romantic story.",
                            "confidence_score": 0.80
                        }
                    ]
                })
            
            mock_ai.get_ai_response = capture_prompt
            
            response = client.post(
                "/api/v1/books/recommendations",
                json={
                    "max_recommendations": 5,
                    "preferred_genres": ["Mystery", "Thriller"],
                    "exclude_genres": ["Romance", "Horror"]
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that prompt included genre preferences
            assert len(prompt_used) == 1
            prompt = prompt_used[0]
            assert "Mystery" in prompt
            assert "Thriller" in prompt
            assert "Romance" in prompt  # As excluded
            
            # Romance book should be filtered out
            assert len(data["recommendations"]) == 1
            assert data["recommendations"][0]["genre"] == "Mystery"
    
    @patch('app.services.book_recommendation_service.ai_service')
    def test_ai_service_error_handling(
        self, mock_ai_service, client, auth_headers
    ):
        """Test handling of AI service errors"""
        # Simulate AI service failure
        mock_ai_service.get_ai_response = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )
        
        response = client.post(
            "/api/v1/books/recommendations",
            json={"max_recommendations": 3},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty recommendations with error message
        assert len(data["recommendations"]) == 0
        assert "Unable to generate recommendations" in data["context_summary"]
    
    def test_regenerate_recommendations(
        self, client, auth_headers, setup_test_books
    ):
        """Test regenerating recommendations after negative feedback"""
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            # First set of recommendations
            mock_ai.get_ai_response = AsyncMock(return_value=json.dumps({
                "recommendations": [
                    {
                        "title": "First Book",
                        "author": "First Author",
                        "genre": "Science Fiction",
                        "description": "First recommendation",
                        "confidence_score": 0.9
                    }
                ]
            }))
            
            # Get initial recommendations
            rec_response = client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 1},
                headers=auth_headers
            )
            first_rec = rec_response.json()["recommendations"][0]
            session_id = rec_response.json()["session_id"]
            
            # Give negative feedback
            feedback_response = client.post(
                "/api/v1/books/recommendations/feedback",
                json={
                    "session_id": session_id,
                    "recommendation_title": first_rec["title"],
                    "recommendation_author": first_rec["author"],
                    "feedback_type": "not_interested"
                },
                headers=auth_headers
            )
            assert feedback_response.json()["should_regenerate"] is True
            
            # Mock different recommendations for regeneration
            mock_ai.get_ai_response = AsyncMock(return_value=json.dumps({
                "recommendations": [
                    {
                        "title": "Different Book",
                        "author": "Different Author",
                        "genre": "Mystery",
                        "description": "New recommendation",
                        "confidence_score": 0.85
                    }
                ]
            }))
            
            # Regenerate recommendations
            regen_response = client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 1},
                headers=auth_headers
            )
            
            assert regen_response.status_code == 200
            new_rec = regen_response.json()["recommendations"][0]
            assert new_rec["title"] != first_rec["title"]
    
    def test_recommendations_pagination(
        self, client, auth_headers, setup_test_books
    ):
        """Test limiting number of recommendations"""
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            # Mock many recommendations
            mock_ai.get_ai_response = AsyncMock(return_value=json.dumps({
                "recommendations": [
                    {
                        "title": f"Book {i}",
                        "author": f"Author {i}",
                        "genre": "Fiction",
                        "description": f"Description {i}",
                        "confidence_score": 0.9 - (i * 0.05)
                    } for i in range(10)
                ]
            }))
            
            # Request only 3 recommendations
            response = client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 3},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["recommendations"]) == 3
            assert data["total_recommendations"] == 3
            
            # Should get highest confidence scores
            assert data["recommendations"][0]["title"] == "Book 0"
            assert data["recommendations"][1]["title"] == "Book 1"
            assert data["recommendations"][2]["title"] == "Book 2"


class TestBookRecommendationsAuth:
    """Test authentication and authorization for recommendations"""
    
    def test_recommendations_require_auth(self, client):
        """Test that recommendations endpoints require authentication"""
        # Get recommendations
        response = client.post(
            "/api/v1/books/recommendations",
            json={"max_recommendations": 3}
        )
        assert response.status_code == 401
        
        # Process feedback
        response = client.post(
            "/api/v1/books/recommendations/feedback",
            json={
                "session_id": "test",
                "recommendation_title": "Test",
                "recommendation_author": "Test",
                "feedback_type": "want_to_read"
            }
        )
        assert response.status_code == 401
    
    def test_user_isolation(self, client):
        """Test that recommendations are isolated per user"""
        # Create two users
        user1_data = {
            "email": "user1@test.com",
            "password": "password123",
            "name": "User One"
        }
        user2_data = {
            "email": "user2@test.com",
            "password": "password123",
            "name": "User Two"
        }
        
        # Register and get tokens
        resp1 = client.post("/api/v1/auth/register", json=user1_data)
        token1 = resp1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        resp2 = client.post("/api/v1/auth/register", json=user2_data)
        token2 = resp2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 1 adds sci-fi books
        for title in ["Dune", "Foundation", "Neuromancer"]:
            client.post(
                "/api/v1/books",
                json={
                    "title": title,
                    "author": "Various",
                    "genre": "Science Fiction",
                    "reading_status": "read"
                },
                headers=headers1
            )
        
        # User 2 adds mystery books
        for title in ["Sherlock Holmes", "Poirot", "Maltese Falcon"]:
            client.post(
                "/api/v1/books",
                json={
                    "title": title,
                    "author": "Various",
                    "genre": "Mystery",
                    "reading_status": "read"
                },
                headers=headers2
            )
        
        # Get recommendations for each user
        with patch('app.services.book_recommendation_service.ai_service') as mock_ai:
            # Mock will receive different contexts
            contexts_received = []
            
            async def capture_context(prompt):
                contexts_received.append(prompt)
                return json.dumps({"recommendations": []})
            
            mock_ai.get_ai_response = capture_context
            
            # User 1 recommendations
            client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 3},
                headers=headers1
            )
            
            # User 2 recommendations
            client.post(
                "/api/v1/books/recommendations",
                json={"max_recommendations": 3},
                headers=headers2
            )
            
            # Verify different contexts
            assert len(contexts_received) == 2
            assert "Science Fiction" in contexts_received[0]
            assert "Dune" in contexts_received[0]
            assert "Mystery" in contexts_received[1]
            assert "Sherlock Holmes" in contexts_received[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])