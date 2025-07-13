"""
Books API - Content management for reading collection
"""
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from ..db.database import get_db
from ..core.auth_service import AuthService
from ..models.content import Book
from ..schemas.books import BookCreate, BookUpdate, BookResponse, BookListResponse, BookFilters, ReadingStatus, BookDetailsRequest, BookDetailsResponse

router = APIRouter(tags=["books"])
logger = logging.getLogger(__name__)


def get_current_user_simple(authorization: str = Header(None)):
    """Simple auth helper"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        token = authorization.split(" ")[1]
        user = AuthService.verify_user_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("", response_model=BookResponse)
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Add a new book to user's collection"""
    try:
        logger.info(f"📖 Adding book: {book_data.title} by {book_data.author}")
        
        user_uuid = uuid.UUID(current_user["id"])
        
        # Create book
        book = Book(
            user_id=user_uuid,
            title=book_data.title,
            author=book_data.author,
            description=book_data.description,
            genre=book_data.genre,
            isbn=book_data.isbn,
            pages=book_data.pages,
            publication_year=book_data.publication_year,
            cover_image_url=book_data.cover_image_url,
            google_books_id=book_data.google_books_id,
            open_library_id=book_data.open_library_id,
            current_page=book_data.current_page,
            reading_status=book_data.reading_status,
            date_started=book_data.date_started,
            date_finished=book_data.date_finished,
            user_notes=book_data.user_notes,
            is_favorite=book_data.is_favorite,
            source=book_data.source
        )
        
        db.add(book)
        db.commit()
        db.refresh(book)
        
        logger.info(f"✅ Book added: {book.id} - {book.title}")
        
        return BookResponse(
            id=str(book.id),
            user_id=str(book.user_id),
            title=book.title,
            author=book.author,
            description=book.description,
            genre=book.genre,
            isbn=book.isbn,
            pages=book.pages,
            publication_year=book.publication_year,
            cover_image_url=book.cover_image_url,
            google_books_id=book.google_books_id,
            open_library_id=book.open_library_id,
            current_page=book.current_page,
            reading_status=book.reading_status,
            date_started=book.date_started,
            date_finished=book.date_finished,
            user_notes=book.user_notes,
            is_favorite=book.is_favorite,
            source=book.source,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Add book error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add book: {str(e)}")


@router.get("", response_model=BookListResponse)
def list_books(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reading_status: Optional[ReadingStatus] = Query(None),
    genre: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get user's book collection with filtering and pagination"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        logger.info(f"📚 Fetching books for user: {user_uuid}")
        
        # Build query
        query = db.query(Book).filter(Book.user_id == user_uuid)
        
        # Apply filters
        if reading_status:
            query = query.filter(Book.reading_status == reading_status)
        
        if genre:
            query = query.filter(Book.genre.ilike(f"%{genre}%"))
            
        if is_favorite is not None:
            query = query.filter(Book.is_favorite == is_favorite)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term),
                    Book.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        books = query.order_by(desc(Book.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"📚 Found {len(books)} books (page {page}/{total_pages}, total: {total})")
        
        # Convert to response format
        book_responses = [
            BookResponse(
                id=str(book.id),
                user_id=str(book.user_id),
                title=book.title,
                author=book.author,
                description=book.description,
                genre=book.genre,
                isbn=book.isbn,
                pages=book.pages,
                publication_year=book.publication_year,
                cover_image_url=book.cover_image_url,
                google_books_id=book.google_books_id,
                open_library_id=book.open_library_id,
                current_page=book.current_page,
                reading_status=book.reading_status,
                date_started=book.date_started,
                date_finished=book.date_finished,
                user_notes=book.user_notes,
                is_favorite=book.is_favorite,
                source=book.source,
                created_at=book.created_at,
                updated_at=book.updated_at
            )
            for book in books
        ]
        
        return BookListResponse(
            books=book_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ List books error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list books: {str(e)}")


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get a specific book by ID"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        book_uuid = uuid.UUID(book_id)
        
        book = db.query(Book).filter(
            Book.id == book_uuid,
            Book.user_id == user_uuid
        ).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return BookResponse(
            id=str(book.id),
            user_id=str(book.user_id),
            title=book.title,
            author=book.author,
            description=book.description,
            genre=book.genre,
            isbn=book.isbn,
            pages=book.pages,
            publication_year=book.publication_year,
            cover_image_url=book.cover_image_url,
            google_books_id=book.google_books_id,
            open_library_id=book.open_library_id,
            current_page=book.current_page,
            reading_status=book.reading_status,
            date_started=book.date_started,
            date_finished=book.date_finished,
            user_notes=book.user_notes,
            is_favorite=book.is_favorite,
            source=book.source,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get book error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get book: {str(e)}")


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: str,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update a book in user's collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        book_uuid = uuid.UUID(book_id)
        
        book = db.query(Book).filter(
            Book.id == book_uuid,
            Book.user_id == user_uuid
        ).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Update fields
        update_data = book_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
        
        db.commit()
        db.refresh(book)
        
        logger.info(f"✏️ Book updated: {book_uuid} - {book.title}")
        
        return BookResponse(
            id=str(book.id),
            user_id=str(book.user_id),
            title=book.title,
            author=book.author,
            description=book.description,
            genre=book.genre,
            isbn=book.isbn,
            pages=book.pages,
            publication_year=book.publication_year,
            cover_image_url=book.cover_image_url,
            google_books_id=book.google_books_id,
            open_library_id=book.open_library_id,
            current_page=book.current_page,
            reading_status=book.reading_status,
            date_started=book.date_started,
            date_finished=book.date_finished,
            user_notes=book.user_notes,
            is_favorite=book.is_favorite,
            source=book.source,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update book error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update book: {str(e)}")


@router.delete("/{book_id}")
def delete_book(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Remove a book from user's collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        book_uuid = uuid.UUID(book_id)
        
        book = db.query(Book).filter(
            Book.id == book_uuid,
            Book.user_id == user_uuid
        ).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        db.delete(book)
        db.commit()
        
        logger.info(f"🗑️ Book deleted: {book_uuid} - {book.title}")
        return {"message": "Book deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete book error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")


@router.patch("/{book_id}/reading-progress")
def update_reading_progress(
    book_id: str,
    current_page: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update reading progress for a book"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        book_uuid = uuid.UUID(book_id)
        
        book = db.query(Book).filter(
            Book.id == book_uuid,
            Book.user_id == user_uuid
        ).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Update current page
        book.current_page = current_page
        
        # Auto-update reading status based on progress
        if current_page == 0:
            book.reading_status = ReadingStatus.WANT_TO_READ
        elif book.pages and current_page >= book.pages:
            book.reading_status = ReadingStatus.READ
            if not book.date_finished:
                from datetime import datetime
                book.date_finished = datetime.utcnow()
        else:
            book.reading_status = ReadingStatus.READING
            if not book.date_started:
                from datetime import datetime
                book.date_started = datetime.utcnow()
        
        db.commit()
        
        progress_percent = 0
        if book.pages and book.pages > 0:
            progress_percent = round((current_page / book.pages) * 100, 1)
        
        logger.info(f"📖 Reading progress updated: {book.title} - page {current_page} ({progress_percent}%)")
        
        return {
            "message": "Reading progress updated",
            "current_page": current_page,
            "total_pages": book.pages,
            "progress_percent": progress_percent,
            "reading_status": book.reading_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update reading progress error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update reading progress: {str(e)}")


@router.get("/debug/health")
def books_health_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Health check endpoint for books system"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        book_count = db.query(Book).filter(Book.user_id == user_uuid).count()
        
        return {
            "status": "healthy",
            "service": "books",
            "user_id": str(user_uuid),
            "user_book_count": book_count,
            "database_connected": True,
            "table_accessible": True
        }
        
    except Exception as e:
        logger.error(f"❌ Books health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "books",
            "error": str(e),
            "database_connected": False,
            "table_accessible": False
        }


@router.post("/fetch-details", response_model=BookDetailsResponse)
async def fetch_book_details(
    request: BookDetailsRequest,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Fetch book details using AI and external APIs
    
    This endpoint accepts a book title and optional author name,
    then uses AI services and external APIs to fetch comprehensive
    book information including publication year, pages, genre,
    description, ISBN, and cover image.
    """
    try:
        logger.info(f"📚 Fetching book details for: {request.title} by {request.author or 'Unknown Author'}")
        
        # Import here to avoid circular imports
        from ..services.book_details_service import book_details_service
        
        # Fetch book details from multiple sources
        book_data = await book_details_service.fetch_book_details(request.title, request.author)
        
        if not book_data:
            raise HTTPException(
                status_code=404, 
                detail="Could not find book details for the provided title and author"
            )
        
        # Convert to response format
        response = BookDetailsResponse(
            title=book_data.get('title', request.title),
            author=book_data.get('author', request.author or ''),
            publication_year=book_data.get('publication_year'),
            pages=book_data.get('pages'),
            genre=book_data.get('genre'),
            description=book_data.get('description'),
            isbn=book_data.get('isbn'),
            cover_image_url=book_data.get('cover_image_url'),
            google_books_id=book_data.get('google_books_id'),
            open_library_id=book_data.get('open_library_id'),
            confidence=book_data.get('confidence'),
            sources=book_data.get('sources', [])
        )
        
        logger.info(f"✅ Successfully fetched book details for: {request.title}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fetch book details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch book details: {str(e)}")