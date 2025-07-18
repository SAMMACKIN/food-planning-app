"""
Goodreads CSV Import Service
"""
import csv
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.content import Book
from ..schemas.books import ReadingStatus


class GoodreadsImportService:
    """Service for importing books from Goodreads CSV export"""
    
    def __init__(self):
        # Map Goodreads shelf names to our reading status
        self.shelf_mapping = {
            'read': ReadingStatus.READ,
            'currently-reading': ReadingStatus.READING,
            'to-read': ReadingStatus.WANT_TO_READ
        }
    
    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse Goodreads CSV content and return list of book data"""
        books = []
        
        # Use StringIO to read CSV content
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Extract shelf name (remove position info like "(#14)")
            exclusive_shelf = row.get('Exclusive Shelf', '').strip()
            if '(' in exclusive_shelf:
                exclusive_shelf = exclusive_shelf.split('(')[0].strip()
            
            # Map to our reading status
            reading_status = self.shelf_mapping.get(
                exclusive_shelf, 
                ReadingStatus.WANT_TO_READ  # Default to want_to_read
            )
            
            # Parse dates
            date_read = self._parse_date(row.get('Date Read', ''))
            date_added = self._parse_date(row.get('Date Added', ''))
            
            # Extract book data
            book_data = {
                'goodreads_id': row.get('Book Id', ''),
                'title': row.get('Title', '').strip(),
                'author': row.get('Author', '').strip(),
                'isbn': self._clean_isbn(row.get('ISBN', '')),
                'isbn13': self._clean_isbn(row.get('ISBN13', '')),
                'my_rating': self._parse_rating(row.get('My Rating', '0')),
                'average_rating': self._parse_float(row.get('Average Rating', '0')),
                'publisher': row.get('Publisher', '').strip(),
                'binding': row.get('Binding', '').strip(),
                'pages': self._parse_int(row.get('Number of Pages', '0')),
                'year_published': self._parse_int(row.get('Year Published', '0')),
                'original_publication_year': self._parse_int(row.get('Original Publication Year', '0')),
                'date_read': date_read,
                'date_added': date_added,
                'bookshelves': row.get('Bookshelves', '').strip(),
                'exclusive_shelf': exclusive_shelf,
                'reading_status': reading_status,
                'my_review': row.get('My Review', '').strip(),
                'private_notes': row.get('Private Notes', '').strip(),
                'read_count': self._parse_int(row.get('Read Count', '0'))
            }
            
            # Only add if we have at least a title
            if book_data['title']:
                books.append(book_data)
        
        return books
    
    async def import_books(
        self, 
        user_id: str, 
        csv_content: str,
        db: Session
    ) -> Dict[str, Any]:
        """Import books from Goodreads CSV content"""
        try:
            # Parse CSV
            parsed_books = self.parse_csv_content(csv_content)
            
            if not parsed_books:
                return {
                    'success': False,
                    'message': 'No valid books found in CSV',
                    'imported': 0,
                    'skipped': 0,
                    'errors': 0
                }
            
            imported = 0
            skipped = 0
            errors = 0
            
            for book_data in parsed_books:
                try:
                    # Check if book already exists for this user
                    existing = db.query(Book).filter(
                        and_(
                            Book.user_id == user_id,
                            Book.title == book_data['title'],
                            Book.author == book_data['author']
                        )
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Create new book
                    book = Book(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        title=book_data['title'],
                        author=book_data['author'],
                        isbn=book_data['isbn'] or book_data['isbn13'],
                        pages=book_data['pages'] if book_data['pages'] > 0 else None,
                        publication_year=book_data['original_publication_year'] or book_data['year_published'],
                        reading_status=book_data['reading_status'],
                        date_started=book_data['date_added'] if book_data['reading_status'] == ReadingStatus.READING else None,
                        date_finished=book_data['date_read'] if book_data['reading_status'] == ReadingStatus.READ else None,
                        user_notes=book_data['private_notes'] or book_data['my_review'],
                        source='goodreads_import',
                        # Add Goodreads metadata
                        description=f"Publisher: {book_data['publisher']}" if book_data.get('publisher') else None
                    )
                    
                    db.add(book)
                    db.flush()  # Get the book ID before committing
                    
                    # Add rating if available
                    if book_data.get('my_rating'):
                        from ..models.content import ContentRating, ContentType
                        rating = ContentRating(
                            user_id=user_id,
                            book_id=book.id,
                            content_type=ContentType.BOOK,
                            rating=book_data['my_rating'],
                            review_text=book_data.get('my_review')
                        )
                        db.add(rating)
                    
                    # Add genre from bookshelves if available
                    if book_data['bookshelves']:
                        # Try to extract a genre from bookshelves
                        shelves = book_data['bookshelves'].split(',')
                        for shelf in shelves:
                            shelf = shelf.strip().lower()
                            # Common genre mappings
                            genre_mappings = {
                                'fiction': 'Fiction',
                                'non-fiction': 'Non-Fiction',
                                'nonfiction': 'Non-Fiction',
                                'fantasy': 'Fantasy',
                                'science-fiction': 'Science Fiction',
                                'sci-fi': 'Science Fiction',
                                'mystery': 'Mystery',
                                'romance': 'Romance',
                                'historical-fiction': 'Historical Fiction',
                                'biography': 'Biography',
                                'history': 'History',
                                'self-help': 'Self-Help',
                                'business': 'Business',
                                'psychology': 'Psychology',
                                'philosophy': 'Philosophy',
                                'memoir': 'Memoir',
                                'thriller': 'Thriller',
                                'horror': 'Horror',
                                'poetry': 'Poetry',
                                'classic': 'Classic Literature',
                                'young-adult': 'Young Adult',
                                'ya': 'Young Adult'
                            }
                            
                            if shelf in genre_mappings:
                                book.genre = genre_mappings[shelf]
                                break
                    
                    imported += 1
                    
                except Exception as e:
                    print(f"Error importing book '{book_data.get('title', 'Unknown')}': {e}")
                    errors += 1
            
            # Commit all books
            db.commit()
            
            return {
                'success': True,
                'message': f'Successfully imported {imported} books',
                'imported': imported,
                'skipped': skipped,
                'errors': errors,
                'total': len(parsed_books)
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error during Goodreads import: {e}")
            return {
                'success': False,
                'message': f'Import failed: {str(e)}',
                'imported': 0,
                'skipped': 0,
                'errors': 0
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from Goodreads format (YYYY/MM/DD)"""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            # Goodreads uses YYYY/MM/DD format
            return datetime.strptime(date_str.strip(), '%Y/%m/%d')
        except:
            return None
    
    def _parse_int(self, value: str) -> int:
        """Parse integer from string"""
        try:
            return int(value)
        except:
            return 0
    
    def _parse_float(self, value: str) -> float:
        """Parse float from string"""
        try:
            return float(value)
        except:
            return 0.0
    
    def _parse_rating(self, value: str) -> Optional[int]:
        """Parse rating (0 means not rated)"""
        rating = self._parse_int(value)
        return rating if rating > 0 else None
    
    def _clean_isbn(self, isbn: str) -> Optional[str]:
        """Clean ISBN from Goodreads format (removes = and quotes)"""
        if not isbn:
            return None
        
        # Remove equals signs and quotes
        cleaned = isbn.strip().strip('=').strip('"').strip("'")
        
        # Return None if empty or just zeros
        if not cleaned or cleaned == '0' or cleaned == '':
            return None
            
        return cleaned


# Create singleton instance
goodreads_import_service = GoodreadsImportService()