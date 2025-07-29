"""
Tests for Book Details Service
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime, timedelta
import time

from app.services.book_details_service import BookDetailsService, book_details_service


class TestBookDetailsService:
    """Test cases for BookDetailsService"""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test"""
        service = BookDetailsService()
        service._cache.clear()  # Clear cache
        return service
    
    @pytest.fixture
    def sample_ai_data(self):
        """Sample AI extracted book data"""
        return {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'genre': 'Fiction',
            'publication_year': 1925,
            'description': 'A classic American novel about the Jazz Age'
        }
    
    @pytest.fixture
    def sample_openlibrary_data(self):
        """Sample Open Library API data"""
        return {
            'open_library_id': 'OL27194W',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'publication_year': 1925,
            'isbn': '9780743273565',
            'cover_image_url': 'https://covers.openlibrary.org/b/id/12345-L.jpg'
        }
    
    @pytest.fixture
    def sample_google_books_data(self):
        """Sample Google Books API data"""
        return {
            'google_books_id': 'abc123',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'publication_year': 1925,
            'pages': 180,
            'description': 'The exemplary novel of the Jazz Age',
            'isbn': '9780743273565',
            'cover_image_url': 'https://books.google.com/books/content?id=abc123'
        }
    
    @pytest.mark.asyncio
    async def test_fetch_book_details_success(self, service, sample_ai_data, sample_openlibrary_data, sample_google_books_data):
        """Test successful book details fetching from all sources"""
        with patch('app.services.book_details_service.ai_service') as mock_ai_service:
            # Mock AI service
            mock_ai_service.extract_book_details = AsyncMock(return_value=sample_ai_data)
            
            # Mock API calls
            with patch.object(service, '_fetch_open_library_data', new_callable=AsyncMock) as mock_ol:
                mock_ol.return_value = sample_openlibrary_data
                
                with patch.object(service, '_fetch_google_books_data', new_callable=AsyncMock) as mock_gb:
                    mock_gb.return_value = sample_google_books_data
                    
                    result = await service.fetch_book_details('The Great Gatsby', 'F. Scott Fitzgerald')
                    
                    # Verify all sources were called
                    mock_ai_service.extract_book_details.assert_called_once_with('The Great Gatsby', 'F. Scott Fitzgerald')
                    mock_ol.assert_called_once_with('The Great Gatsby', 'F. Scott Fitzgerald')
                    mock_gb.assert_called_once_with('The Great Gatsby', 'F. Scott Fitzgerald')
                    
                    # Verify merged data
                    assert result is not None
                    assert result['title'] == 'The Great Gatsby'
                    assert result['author'] == 'F. Scott Fitzgerald'
                    assert result['cover_image_url'] == sample_openlibrary_data['cover_image_url']  # OL preferred
                    assert result['pages'] == 180  # From Google Books
                    assert result['sources'] == ['ai', 'openlibrary', 'google_books']
    
    @pytest.mark.asyncio
    async def test_fetch_book_details_with_cache(self, service):
        """Test cache functionality"""
        # First call - populate cache
        with patch('app.services.book_details_service.ai_service') as mock_ai_service:
            mock_ai_service.extract_book_details = AsyncMock(return_value={'title': 'Test Book', 'author': 'Test Author'})
            
            with patch.object(service, '_fetch_open_library_data', new_callable=AsyncMock) as mock_ol:
                mock_ol.return_value = None
                
                with patch.object(service, '_fetch_google_books_data', new_callable=AsyncMock) as mock_gb:
                    mock_gb.return_value = None
                    
                    result1 = await service.fetch_book_details('Test Book', 'Test Author')
                    assert result1 is not None
                    
                    # Second call - should use cache
                    result2 = await service.fetch_book_details('Test Book', 'Test Author')
                    
                    # Verify APIs were only called once
                    assert mock_ai_service.extract_book_details.call_count == 1
                    assert mock_ol.call_count == 1
                    assert mock_gb.call_count == 1
                    
                    # Results should be identical
                    assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_fetch_open_library_data(self, service):
        """Test Open Library API integration"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'docs': [
                {
                    'key': '/works/OL27194W',
                    'title': 'The Great Gatsby',
                    'author_name': ['F. Scott Fitzgerald'],
                    'first_publish_year': 1925,
                    'isbn': ['9780743273565'],
                    'cover_i': 12345
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await service._fetch_open_library_data('The Great Gatsby', 'F. Scott Fitzgerald')
            
            assert result is not None
            assert result['open_library_id'] == 'OL27194W'
            assert result['title'] == 'The Great Gatsby'
            assert result['author'] == 'F. Scott Fitzgerald'
            assert result['publication_year'] == 1925
            assert result['isbn'] == '9780743273565'
            assert 'covers.openlibrary.org' in result['cover_image_url']
    
    @pytest.mark.asyncio
    async def test_fetch_google_books_data(self, service):
        """Test Google Books API integration"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 'abc123',
                    'volumeInfo': {
                        'title': 'The Great Gatsby',
                        'authors': ['F. Scott Fitzgerald'],
                        'publishedDate': '1925-04-10',
                        'pageCount': 180,
                        'description': 'A classic novel',
                        'industryIdentifiers': [
                            {'type': 'ISBN_13', 'identifier': '9780743273565'}
                        ],
                        'imageLinks': {
                            'thumbnail': 'http://books.google.com/thumbnail',
                            'large': 'http://books.google.com/large'
                        }
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await service._fetch_google_books_data('The Great Gatsby', 'F. Scott Fitzgerald')
            
            assert result is not None
            assert result['google_books_id'] == 'abc123'
            assert result['title'] == 'The Great Gatsby'
            assert result['author'] == 'F. Scott Fitzgerald'
            assert result['publication_year'] == 1925
            assert result['pages'] == 180
            assert result['isbn'] == '9780743273565'
            assert result['cover_image_url'] == 'http://books.google.com/large'
    
    @pytest.mark.asyncio
    async def test_api_failure_handling(self, service):
        """Test handling of API failures"""
        with patch('app.services.book_details_service.ai_service') as mock_ai_service:
            # AI service fails
            mock_ai_service.extract_book_details = AsyncMock(side_effect=Exception("AI service error"))
            
            # Open Library fails
            with patch.object(service, '_fetch_open_library_data', new_callable=AsyncMock) as mock_ol:
                mock_ol.side_effect = httpx.HTTPError("Network error")
                
                # Google Books succeeds
                with patch.object(service, '_fetch_google_books_data', new_callable=AsyncMock) as mock_gb:
                    mock_gb.return_value = {
                        'title': 'Fallback Book',
                        'author': 'Fallback Author',
                        'pages': 100
                    }
                    
                    result = await service.fetch_book_details('Test Book')
                    
                    # Should still return Google Books data
                    assert result is not None
                    assert result['title'] == 'Fallback Book'
                    assert result['author'] == 'Fallback Author'
                    assert result['sources'] == ['google_books']
    
    def test_find_best_book_match(self, service):
        """Test book matching algorithm"""
        docs = [
            {
                'title': 'The Great Gatsby',
                'author_name': ['F. Scott Fitzgerald']
            },
            {
                'title': 'Gatsby: A Novel',
                'author_name': ['Someone Else']
            },
            {
                'title': 'Something Completely Different',
                'author_name': ['Random Author']
            }
        ]
        
        # Test exact title match
        best_match = service._find_best_book_match(docs, 'The Great Gatsby', 'F. Scott Fitzgerald')
        assert best_match['title'] == 'The Great Gatsby'
        
        # Test partial match
        best_match = service._find_best_book_match(docs, 'Gatsby', None)
        assert 'Gatsby' in best_match['title']
        
        # Test no good match returns first result
        best_match = service._find_best_book_match(docs, 'Nonexistent Book', 'Unknown Author')
        assert best_match == docs[0]
    
    def test_extract_year(self, service):
        """Test year extraction from various date formats"""
        assert service._extract_year('1925') == 1925
        assert service._extract_year('1925-04') == 1925
        assert service._extract_year('1925-04-10') == 1925
        assert service._extract_year('') is None
        assert service._extract_year(None) is None
        assert service._extract_year('invalid') is None
    
    def test_merge_book_data(self, service):
        """Test data merging logic"""
        ai_data = {
            'title': 'AI Title',
            'author': 'AI Author',
            'genre': 'Fiction',
            'description': 'AI description'
        }
        
        openlibrary_data = {
            'title': 'OL Title',
            'author': 'OL Author',
            'isbn': '1234567890',
            'cover_image_url': 'https://ol-cover.jpg',
            'open_library_id': 'OL123'
        }
        
        google_books_data = {
            'title': 'GB Title',
            'author': 'GB Author',
            'pages': 200,
            'cover_image_url': 'https://gb-cover.jpg',
            'google_books_id': 'GB123'
        }
        
        # Test merging all sources
        result = service._merge_book_data(ai_data, openlibrary_data, google_books_data)
        
        # AI data is base
        assert result['title'] == 'AI Title'
        assert result['author'] == 'AI Author'
        assert result['genre'] == 'Fiction'
        
        # Open Library preferred for cover
        assert result['cover_image_url'] == 'https://ol-cover.jpg'
        assert result['open_library_id'] == 'OL123'
        
        # Google Books fills gaps
        assert result['pages'] == 200
        assert result['google_books_id'] == 'GB123'
        
        # ISBN from Open Library (AI didn't have it)
        assert result['isbn'] == '1234567890'
        
        # Sources tracked
        assert set(result['sources']) == {'ai', 'openlibrary', 'google_books'}
    
    def test_merge_book_data_missing_ai(self, service):
        """Test merging when AI data is missing"""
        openlibrary_data = {
            'title': 'OL Title',
            'author': 'OL Author',
            'cover_image_url': 'https://ol-cover.jpg'
        }
        
        google_books_data = {
            'pages': 200,
            'description': 'Google description'
        }
        
        result = service._merge_book_data(None, openlibrary_data, google_books_data)
        
        assert result['title'] == 'OL Title'
        assert result['author'] == 'OL Author'
        assert result['pages'] == 200
        assert result['description'] == 'Google description'
        assert set(result['sources']) == {'openlibrary', 'google_books'}
    
    def test_cache_functionality(self, service):
        """Test cache operations"""
        cache_key = service._get_cache_key('Test Book', 'Test Author')
        test_data = {'title': 'Test Book', 'author': 'Test Author'}
        
        # Test cache miss
        assert service._get_from_cache(cache_key) is None
        
        # Test cache save and retrieve
        service._save_to_cache(cache_key, test_data)
        cached = service._get_from_cache(cache_key)
        assert cached == test_data
        
        # Test cache expiration
        # Manually set old timestamp
        service._cache[cache_key]['timestamp'] = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
        assert service._get_from_cache(cache_key) is None
        assert cache_key not in service._cache  # Should be removed
    
    def test_cache_key_generation(self, service):
        """Test cache key generation"""
        # With author
        key1 = service._get_cache_key('The Great Gatsby', 'F. Scott Fitzgerald')
        assert key1 == 'the great gatsby|f. scott fitzgerald'
        
        # Without author
        key2 = service._get_cache_key('The Great Gatsby', None)
        assert key2 == 'the great gatsby'
        
        # Case and whitespace normalization
        key3 = service._get_cache_key('  THE GREAT GATSBY  ', '  F. SCOTT FITZGERALD  ')
        assert key3 == 'the great gatsby|f. scott fitzgerald'
    
    def test_cache_size_limit(self, service):
        """Test cache size limiting"""
        # Fill cache beyond limit
        for i in range(1005):
            service._save_to_cache(f'book_{i}', {'title': f'Book {i}'})
        
        # Should maintain max size
        assert len(service._cache) <= 1000
        
        # Oldest entries should be removed
        assert 'book_0' not in service._cache
        assert 'book_1004' in service._cache
    
    @pytest.mark.asyncio
    async def test_no_results_handling(self, service):
        """Test handling when no book details are found"""
        with patch('app.services.book_details_service.ai_service') as mock_ai_service:
            mock_ai_service.extract_book_details = AsyncMock(return_value=None)
            
            with patch.object(service, '_fetch_open_library_data', new_callable=AsyncMock) as mock_ol:
                mock_ol.return_value = None
                
                with patch.object(service, '_fetch_google_books_data', new_callable=AsyncMock) as mock_gb:
                    mock_gb.return_value = None
                    
                    result = await service.fetch_book_details('Nonexistent Book')
                    assert result is None
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, service):
        """Test general exception handling"""
        with patch('app.services.book_details_service.ai_service') as mock_ai_service:
            # Simulate import error
            mock_ai_service.extract_book_details = Mock(side_effect=ImportError("Module not found"))
            
            result = await service.fetch_book_details('Test Book')
            assert result is None  # Should handle gracefully
    
    def test_global_instance(self):
        """Test global service instance"""
        assert book_details_service is not None
        assert isinstance(book_details_service, BookDetailsService)
        assert book_details_service.timeout == 30.0
        assert book_details_service.cache_duration == 30 * 24 * 60 * 60