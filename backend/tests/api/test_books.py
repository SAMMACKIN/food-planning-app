"""
Test suite for Books API endpoints
"""
import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import create_app
from app.models.content import Book
from app.schemas.books import ReadingStatus


class TestBooksAPI:
    """Test Books API endpoints"""
    
    def test_create_book(self, client: TestClient, auth_headers: dict):
        """Test creating a new book"""
        book_data = {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "description": "A classic American novel",
            "genre": "Fiction",
            "isbn": "9780743273565",
            "pages": 180,
            "publication_year": 1925,
            "reading_status": "want_to_read"
        }
        
        response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["reading_status"] == book_data["reading_status"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_book_minimal(self, client: TestClient, auth_headers: dict):
        """Test creating a book with minimal required fields"""
        book_data = {
            "title": "Minimal Book",
            "author": "Test Author"
        }
        
        response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["reading_status"] == "want_to_read"  # Default
        assert data["current_page"] == 0  # Default
        assert data["is_favorite"] == False  # Default
    
    def test_list_books_empty(self, client: TestClient, auth_headers: dict):
        """Test listing books when user has none"""
        response = client.get(
            "/api/v1/books",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["books"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 0
    
    def test_list_books_with_data(self, client: TestClient, auth_headers: dict, test_db: Session):
        """Test listing books with pagination"""
        # Create test books directly in database
        user_id = uuid.uuid4()  # This should match the test user
        
        books = [
            Book(
                user_id=user_id,
                title=f"Test Book {i}",
                author=f"Author {i}",
                reading_status=ReadingStatus.WANT_TO_READ if i % 2 == 0 else ReadingStatus.READING
            )
            for i in range(5)
        ]
        
        for book in books:
            test_db.add(book)
        test_db.commit()
        
        # Test basic list
        response = client.get(
            "/api/v1/books",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 5
        assert data["total"] == 5
    
    def test_list_books_with_filters(self, client: TestClient, auth_headers: dict):
        """Test listing books with filters"""
        # Create a book first
        book_data = {
            "title": "Fiction Book",
            "author": "Fiction Author",
            "genre": "Science Fiction",
            "reading_status": "reading"
        }
        
        client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        # Test filter by reading status
        response = client.get(
            "/api/v1/books?reading_status=reading",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 1
        assert data["books"][0]["reading_status"] == "reading"
    
    def test_get_book(self, client: TestClient, auth_headers: dict):
        """Test getting a specific book"""
        # Create a book first
        book_data = {
            "title": "Get Test Book",
            "author": "Get Test Author"
        }
        
        create_response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        book_id = create_response.json()["id"]
        
        # Get the book
        response = client.get(
            f"/api/v1/books/{book_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book_id
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
    
    def test_get_book_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent book"""
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/books/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"
    
    def test_update_book(self, client: TestClient, auth_headers: dict):
        """Test updating a book"""
        # Create a book first
        book_data = {
            "title": "Original Title",
            "author": "Original Author",
            "pages": 100
        }
        
        create_response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        book_id = create_response.json()["id"]
        
        # Update the book
        update_data = {
            "title": "Updated Title",
            "pages": 200,
            "reading_status": "reading"
        }
        
        response = client.put(
            f"/api/v1/books/{book_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["pages"] == update_data["pages"]
        assert data["reading_status"] == update_data["reading_status"]
        assert data["author"] == book_data["author"]  # Unchanged
    
    def test_delete_book(self, client: TestClient, auth_headers: dict):
        """Test deleting a book"""
        # Create a book first
        book_data = {
            "title": "Book to Delete",
            "author": "Delete Author"
        }
        
        create_response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        book_id = create_response.json()["id"]
        
        # Delete the book
        response = client.delete(
            f"/api/v1/books/{book_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Book deleted successfully"
        
        # Verify book is gone
        get_response = client.get(
            f"/api/v1/books/{book_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 404
    
    def test_update_reading_progress(self, client: TestClient, auth_headers: dict):
        """Test updating reading progress"""
        # Create a book with pages
        book_data = {
            "title": "Progress Book",
            "author": "Progress Author",
            "pages": 300
        }
        
        create_response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        book_id = create_response.json()["id"]
        
        # Update progress to page 150
        response = client.patch(
            f"/api/v1/books/{book_id}/reading-progress?current_page=150",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == 150
        assert data["total_pages"] == 300
        assert data["progress_percent"] == 50.0
        assert data["reading_status"] == "reading"
    
    def test_update_reading_progress_completion(self, client: TestClient, auth_headers: dict):
        """Test marking book as completed via reading progress"""
        # Create a book with pages
        book_data = {
            "title": "Complete Book",
            "author": "Complete Author",
            "pages": 200
        }
        
        create_response = client.post(
            "/api/v1/books",
            json=book_data,
            headers=auth_headers
        )
        
        book_id = create_response.json()["id"]
        
        # Update progress to completion
        response = client.patch(
            f"/api/v1/books/{book_id}/reading-progress?current_page=200",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == 200
        assert data["progress_percent"] == 100.0
        assert data["reading_status"] == "read"
    
    def test_books_health_check(self, client: TestClient, auth_headers: dict):
        """Test books service health check"""
        response = client.get(
            "/api/v1/books/debug/health",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "books"
        assert "user_book_count" in data
        assert data["database_connected"] == True
        assert data["table_accessible"] == True
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing books API without authentication"""
        response = client.get("/api/v1/books")
        assert response.status_code == 401
        
        response = client.post("/api/v1/books", json={"title": "Test", "author": "Test"})
        assert response.status_code == 401
    
    def test_invalid_book_id(self, client: TestClient, auth_headers: dict):
        """Test accessing book with invalid ID format"""
        response = client.get(
            "/api/v1/books/invalid-uuid",
            headers=auth_headers
        )
        
        assert response.status_code == 500  # UUID parsing error