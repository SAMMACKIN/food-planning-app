"""
Tests for Goodreads Import Service
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import uuid
from sqlalchemy.orm import Session

from app.services.goodreads_import_service import GoodreadsImportService, goodreads_import_service
from app.models.content import Book, ContentRating, ContentType
from app.schemas.books import ReadingStatus


class TestGoodreadsImportService:
    """Test cases for GoodreadsImportService"""
    
    @pytest.fixture
    def service(self):
        """Create a service instance"""
        return GoodreadsImportService()
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample Goodreads CSV content"""
        return """Book Id,Title,Author,Author l-f,Additional Authors,ISBN,ISBN13,My Rating,Average Rating,Publisher,Binding,Number of Pages,Year Published,Original Publication Year,Date Read,Date Added,Bookshelves,Bookshelves with positions,Exclusive Shelf,My Review,Spoiler,Private Notes,Read Count,Owned Copies
12345,The Great Gatsby,F. Scott Fitzgerald,"Fitzgerald, F. Scott",,0743273567,9780743273565,5,3.91,Scribner,Paperback,180,2004,1925,2023/12/25,2023/01/15,"fiction, classics","fiction (#1), classics (#5)",read,"Amazing book about the American Dream",,Personal favorite,1,0
67890,1984,George Orwell,"Orwell, George",,0451524934,9780451524935,4,4.19,Signet Classics,Mass Market Paperback,328,1961,1949,,2023/03/20,"fiction, dystopian, currently-reading","fiction (#2), dystopian (#1), currently-reading (#1)",currently-reading (#1),,,Reading for book club,0,0
11111,To Kill a Mockingbird,Harper Lee,"Lee, Harper",,="0060935464",="9780060935467",0,4.27,Harper Perennial Modern Classics,Paperback,324,2006,1960,,2023/05/10,"to-read, fiction","to-read (#10), fiction (#3)",to-read (#10),,,Want to read this classic,0,0
22222,Invalid Book,,,,,,,0,0.0,,,0,0,0,,,,,,,,,0,0"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    def test_parse_csv_content(self, service, sample_csv_content):
        """Test CSV parsing functionality"""
        books = service.parse_csv_content(sample_csv_content)
        
        assert len(books) == 3  # Invalid book should be filtered out
        
        # Check first book (read)
        gatsby = books[0]
        assert gatsby['title'] == 'The Great Gatsby'
        assert gatsby['author'] == 'F. Scott Fitzgerald'
        assert gatsby['goodreads_id'] == '12345'
        assert gatsby['isbn'] == '0743273567'
        assert gatsby['isbn13'] == '9780743273565'
        assert gatsby['my_rating'] == 5
        assert gatsby['pages'] == 180
        assert gatsby['reading_status'] == ReadingStatus.READ
        assert gatsby['exclusive_shelf'] == 'read'
        assert gatsby['my_review'] == 'Amazing book about the American Dream'
        assert gatsby['private_notes'] == 'Personal favorite'
        assert gatsby['date_read'] == datetime(2023, 12, 25)
        assert gatsby['date_added'] == datetime(2023, 1, 15)
        
        # Check second book (currently reading)
        orwell = books[1]
        assert orwell['title'] == '1984'
        assert orwell['reading_status'] == ReadingStatus.READING
        assert orwell['exclusive_shelf'] == 'currently-reading'
        assert orwell['my_rating'] is None  # 0 rating means not rated
        
        # Check third book (to read)
        mockingbird = books[2]
        assert mockingbird['title'] == 'To Kill a Mockingbird'
        assert mockingbird['reading_status'] == ReadingStatus.WANT_TO_READ
        assert mockingbird['isbn'] == '0060935464'  # Cleaned ISBN
    
    def test_shelf_mapping(self, service):
        """Test Goodreads shelf to reading status mapping"""
        assert service.shelf_mapping['read'] == ReadingStatus.READ
        assert service.shelf_mapping['currently-reading'] == ReadingStatus.READING
        assert service.shelf_mapping['to-read'] == ReadingStatus.WANT_TO_READ
    
    def test_parse_date(self, service):
        """Test date parsing"""
        # Valid date
        assert service._parse_date('2023/12/25') == datetime(2023, 12, 25)
        
        # Empty/invalid dates
        assert service._parse_date('') is None
        assert service._parse_date('   ') is None
        assert service._parse_date('invalid') is None
        assert service._parse_date('2023-12-25') is None  # Wrong format
    
    def test_parse_int(self, service):
        """Test integer parsing"""
        assert service._parse_int('123') == 123
        assert service._parse_int('0') == 0
        assert service._parse_int('') == 0
        assert service._parse_int('abc') == 0
        assert service._parse_int('12.5') == 0  # Invalid int
    
    def test_parse_float(self, service):
        """Test float parsing"""
        assert service._parse_float('3.14') == 3.14
        assert service._parse_float('0') == 0.0
        assert service._parse_float('') == 0.0
        assert service._parse_float('abc') == 0.0
    
    def test_parse_rating(self, service):
        """Test rating parsing"""
        assert service._parse_rating('5') == 5
        assert service._parse_rating('3') == 3
        assert service._parse_rating('0') is None  # 0 means not rated
        assert service._parse_rating('') is None
        assert service._parse_rating('abc') is None
    
    def test_clean_isbn(self, service):
        """Test ISBN cleaning"""
        # Normal ISBN
        assert service._clean_isbn('0743273567') == '0743273567'
        assert service._clean_isbn('9780743273565') == '9780743273565'
        
        # With Excel formatting
        assert service._clean_isbn('="0743273567"') == '0743273567'
        assert service._clean_isbn("='9780743273565'") == '9780743273565'
        assert service._clean_isbn(' ="0743273567" ') == '0743273567'
        
        # Invalid ISBNs
        assert service._clean_isbn('') is None
        assert service._clean_isbn('0') is None
        assert service._clean_isbn('="0"') is None
    
    @pytest.mark.asyncio
    async def test_import_books_success(self, service, mock_db, sample_csv_content):
        """Test successful book import"""
        user_id = str(uuid.uuid4())
        
        # Mock query responses
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existing books
        mock_db.query.return_value = mock_query
        
        # Track added objects
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)
        
        result = await service.import_books(user_id, sample_csv_content, mock_db)
        
        assert result['success'] is True
        assert result['imported'] == 3
        assert result['skipped'] == 0
        assert result['errors'] == 0
        assert result['total'] == 3
        
        # Check books were created
        books = [obj for obj in added_objects if isinstance(obj, Book)]
        assert len(books) == 3
        
        # Check first book details
        gatsby = next(b for b in books if b.title == 'The Great Gatsby')
        assert gatsby.author == 'F. Scott Fitzgerald'
        assert gatsby.isbn == '0743273567'
        assert gatsby.pages == 180
        assert gatsby.publication_year == 1925
        assert gatsby.reading_status == ReadingStatus.READ
        assert gatsby.date_finished == datetime(2023, 12, 25)
        assert gatsby.source == 'goodreads_import'
        
        # Check ratings were created
        ratings = [obj for obj in added_objects if isinstance(obj, ContentRating)]
        assert len(ratings) == 2  # Two books had ratings
        
        gatsby_rating = next(r for r in ratings if r.rating == 5)
        assert gatsby_rating.content_type == ContentType.BOOK
        assert gatsby_rating.review_text == 'Amazing book about the American Dream'
    
    @pytest.mark.asyncio
    async def test_import_books_skip_existing(self, service, mock_db, sample_csv_content):
        """Test skipping existing books"""
        user_id = str(uuid.uuid4())
        
        # Mock existing book
        existing_book = Book(
            title='The Great Gatsby',
            author='F. Scott Fitzgerald',
            user_id=user_id
        )
        
        # Mock query to return existing book for first book only
        call_count = 0
        def query_side_effect(model):
            nonlocal call_count
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            if call_count == 0:
                mock_query.first.return_value = existing_book
            else:
                mock_query.first.return_value = None
            call_count += 1
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = await service.import_books(user_id, sample_csv_content, mock_db)
        
        assert result['success'] is True
        assert result['imported'] == 2  # Only 2 new books
        assert result['skipped'] == 1  # Gatsby was skipped
        assert result['errors'] == 0
    
    @pytest.mark.asyncio
    async def test_import_books_with_genre_extraction(self, service, mock_db):
        """Test genre extraction from bookshelves"""
        csv_content = """Book Id,Title,Author,ISBN,ISBN13,My Rating,Number of Pages,Original Publication Year,Date Read,Date Added,Bookshelves,Exclusive Shelf
12345,Test Book,Test Author,123456,9781234567890,4,200,2020,2023/01/01,2023/01/01,"science-fiction, hugo-awards, space-opera",read"""
        
        user_id = str(uuid.uuid4())
        
        # Mock no existing books
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Track added books
        added_books = []
        mock_db.add.side_effect = lambda obj: added_books.append(obj) if isinstance(obj, Book) else None
        
        result = await service.import_books(user_id, csv_content, mock_db)
        
        assert result['success'] is True
        assert result['imported'] == 1
        
        # Check genre was extracted
        book = added_books[0]
        assert book.genre == 'Science Fiction'  # Mapped from 'science-fiction'
    
    @pytest.mark.asyncio
    async def test_import_books_error_handling(self, service, mock_db):
        """Test error handling during import"""
        user_id = str(uuid.uuid4())
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection error")
        
        result = await service.import_books(user_id, "any csv content", mock_db)
        
        assert result['success'] is False
        assert 'Database connection error' in result['message']
        assert result['imported'] == 0
        assert mock_db.rollback.called
    
    @pytest.mark.asyncio
    async def test_import_books_with_notes_and_reviews(self, service, mock_db):
        """Test importing books with notes and reviews"""
        csv_content = """Book Id,Title,Author,ISBN,My Rating,Exclusive Shelf,My Review,Private Notes
12345,Book With Notes,Author Name,123456,5,read,"This is my review","Private thoughts""""
        
        user_id = str(uuid.uuid4())
        
        # Mock no existing books
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Track added objects
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)
        
        result = await service.import_books(user_id, csv_content, mock_db)
        
        assert result['success'] is True
        
        # Check book has notes
        book = next(obj for obj in added_objects if isinstance(obj, Book))
        assert book.user_notes == "Private thoughts"  # Private notes take precedence
        
        # Check rating has review
        rating = next(obj for obj in added_objects if isinstance(obj, ContentRating))
        assert rating.review_text == "This is my review"
    
    def test_parse_csv_with_shelf_position(self, service):
        """Test parsing CSV with shelf position indicators"""
        csv_content = """Book Id,Title,Author,Exclusive Shelf
12345,Test Book,Test Author,currently-reading (#5)"""
        
        books = service.parse_csv_content(csv_content)
        
        assert len(books) == 1
        assert books[0]['exclusive_shelf'] == 'currently-reading'  # Position removed
        assert books[0]['reading_status'] == ReadingStatus.READING
    
    def test_empty_csv_handling(self, service):
        """Test handling empty CSV"""
        # Just headers
        csv_content = "Book Id,Title,Author"
        books = service.parse_csv_content(csv_content)
        assert len(books) == 0
        
        # Empty string
        books = service.parse_csv_content("")
        assert len(books) == 0
    
    def test_global_instance(self):
        """Test global service instance"""
        assert goodreads_import_service is not None
        assert isinstance(goodreads_import_service, GoodreadsImportService)
        assert hasattr(goodreads_import_service, 'shelf_mapping')