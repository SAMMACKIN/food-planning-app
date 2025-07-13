"""
Book Details Service
Handles AI-powered book details fetching and external API integration
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote
import asyncio

logger = logging.getLogger(__name__)


class BookDetailsService:
    def __init__(self):
        self.timeout = 30.0
        self._cache = {}  # Simple in-memory cache
        self.cache_duration = 30 * 24 * 60 * 60  # 30 days in seconds
        
    async def fetch_book_details(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive book details using AI and external APIs
        """
        try:
            logger.info(f"📚 Fetching book details for: {title} by {author or 'Unknown Author'}")
            
            # Check cache first
            cache_key = self._get_cache_key(title, author)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"📚 Returning cached book details for: {title}")
                return cached_result
            
            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from ai_service import ai_service
            
            # Start AI extraction and external API calls concurrently
            tasks = [
                ai_service.extract_book_details(title, author),
                self._fetch_open_library_data(title, author),
                self._fetch_google_books_data(title, author)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            ai_data, openlibrary_data, google_books_data = results
            
            # Handle exceptions
            if isinstance(ai_data, Exception):
                logger.error(f"AI extraction failed: {ai_data}")
                ai_data = None
            if isinstance(openlibrary_data, Exception):
                logger.error(f"Open Library API failed: {openlibrary_data}")
                openlibrary_data = None
            if isinstance(google_books_data, Exception):
                logger.error(f"Google Books API failed: {google_books_data}")
                google_books_data = None
            
            # Merge data from all sources
            merged_data = self._merge_book_data(ai_data, openlibrary_data, google_books_data)
            
            if merged_data:
                logger.info(f"✅ Successfully fetched book details for: {title}")
                # Cache the result
                self._save_to_cache(cache_key, merged_data)
                return merged_data
            else:
                logger.warning(f"❌ No book details found for: {title}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Book details fetch failed for {title}: {e}")
            return None

    async def _fetch_open_library_data(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch book data from Open Library API"""
        try:
            # Search for the book
            search_query = title
            if author:
                search_query += f" {author}"
            
            search_url = f"https://openlibrary.org/search.json?q={quote(search_query)}&limit=5"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url)
                response.raise_for_status()
                
                search_data = response.json()
                docs = search_data.get('docs', [])
                
                if not docs:
                    return None
                
                # Find the best match
                best_match = self._find_best_book_match(docs, title, author)
                if not best_match:
                    return None
                
                # Extract relevant data
                openlibrary_data = {
                    'open_library_id': best_match.get('key', '').replace('/works/', ''),
                    'title': best_match.get('title'),
                    'author': ', '.join(best_match.get('author_name', [])),
                    'publication_year': best_match.get('first_publish_year'),
                    'isbn': best_match.get('isbn', [None])[0] if best_match.get('isbn') else None,
                    'cover_image_url': None
                }
                
                # Get cover image URL if cover_i is available
                cover_id = best_match.get('cover_i')
                if cover_id:
                    openlibrary_data['cover_image_url'] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                
                logger.info(f"✅ Found Open Library data for: {title}")
                return openlibrary_data
                
        except Exception as e:
            logger.error(f"❌ Open Library API error: {e}")
            return None

    async def _fetch_google_books_data(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch book data from Google Books API"""
        try:
            # Build search query
            search_query = f"intitle:{title}"
            if author:
                search_query += f" inauthor:{author}"
            
            search_url = f"https://www.googleapis.com/books/v1/volumes?q={quote(search_query)}&maxResults=5"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url)
                response.raise_for_status()
                
                search_data = response.json()
                items = search_data.get('items', [])
                
                if not items:
                    return None
                
                # Get the first result (Google Books usually returns best matches first)
                book = items[0]
                volume_info = book.get('volumeInfo', {})
                
                # Extract cover image
                cover_url = None
                image_links = volume_info.get('imageLinks', {})
                if image_links:
                    # Prefer larger images
                    cover_url = (image_links.get('large') or 
                               image_links.get('medium') or 
                               image_links.get('small') or 
                               image_links.get('thumbnail'))
                
                # Extract ISBN
                isbn = None
                industry_identifiers = volume_info.get('industryIdentifiers', [])
                for identifier in industry_identifiers:
                    if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                        isbn = identifier.get('identifier')
                        break
                
                google_books_data = {
                    'google_books_id': book.get('id'),
                    'title': volume_info.get('title'),
                    'author': ', '.join(volume_info.get('authors', [])),
                    'publication_year': self._extract_year(volume_info.get('publishedDate')),
                    'pages': volume_info.get('pageCount'),
                    'description': volume_info.get('description'),
                    'isbn': isbn,
                    'cover_image_url': cover_url
                }
                
                logger.info(f"✅ Found Google Books data for: {title}")
                return google_books_data
                
        except Exception as e:
            logger.error(f"❌ Google Books API error: {e}")
            return None

    def _find_best_book_match(self, docs: List[Dict], title: str, author: Optional[str] = None) -> Optional[Dict]:
        """Find the best matching book from search results"""
        if not docs:
            return None
        
        # Simple scoring based on title similarity
        def score_match(doc):
            score = 0
            doc_title = doc.get('title', '').lower()
            if title.lower() in doc_title or doc_title in title.lower():
                score += 3
            
            if author:
                doc_authors = [name.lower() for name in doc.get('author_name', [])]
                if any(author.lower() in doc_author or doc_author in author.lower() for doc_author in doc_authors):
                    score += 2
            
            return score
        
        # Sort by score and return the best match
        docs_with_scores = [(doc, score_match(doc)) for doc in docs]
        docs_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_match, best_score = docs_with_scores[0]
        return best_match if best_score > 0 else docs[0]  # Return first result if no good match

    def _extract_year(self, published_date: Optional[str]) -> Optional[int]:
        """Extract year from published date string"""
        if not published_date:
            return None
        try:
            # Handle different date formats (YYYY, YYYY-MM, YYYY-MM-DD)
            year_str = published_date.split('-')[0]
            return int(year_str)
        except (ValueError, IndexError):
            return None

    def _merge_book_data(self, ai_data: Optional[Dict], openlibrary_data: Optional[Dict], google_books_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Merge book data from multiple sources with priority"""
        if not any([ai_data, openlibrary_data, google_books_data]):
            return None
        
        # Initialize result with AI data as base (if available)
        result = ai_data.copy() if ai_data else {}
        sources = []
        
        if ai_data:
            sources.append('ai')
        
        # Merge Open Library data
        if openlibrary_data:
            sources.append('openlibrary')
            # Prefer Open Library for cover images and IDs
            if openlibrary_data.get('cover_image_url'):
                result['cover_image_url'] = openlibrary_data['cover_image_url']
            if openlibrary_data.get('open_library_id'):
                result['open_library_id'] = openlibrary_data['open_library_id']
            # Use Open Library ISBN if AI didn't provide one
            if not result.get('isbn') and openlibrary_data.get('isbn'):
                result['isbn'] = openlibrary_data['isbn']
        
        # Merge Google Books data
        if google_books_data:
            sources.append('google_books')
            # Prefer Google Books for cover images if Open Library didn't have one
            if not result.get('cover_image_url') and google_books_data.get('cover_image_url'):
                result['cover_image_url'] = google_books_data['cover_image_url']
            if google_books_data.get('google_books_id'):
                result['google_books_id'] = google_books_data['google_books_id']
            # Use Google Books data if AI didn't provide it
            if not result.get('pages') and google_books_data.get('pages'):
                result['pages'] = google_books_data['pages']
            if not result.get('description') and google_books_data.get('description'):
                result['description'] = google_books_data['description']
            if not result.get('isbn') and google_books_data.get('isbn'):
                result['isbn'] = google_books_data['isbn']
        
        # Ensure we have basic required fields
        if not result.get('title') or not result.get('author'):
            # Try to fill from external APIs
            for data in [openlibrary_data, google_books_data]:
                if data:
                    if not result.get('title'):
                        result['title'] = data.get('title', '')
                    if not result.get('author'):
                        result['author'] = data.get('author', '')
        
        # Add sources list
        result['sources'] = sources
        
        return result if result.get('title') and result.get('author') else None

    def _get_cache_key(self, title: str, author: Optional[str] = None) -> str:
        """Generate cache key from title and author"""
        key = f"{title.lower().strip()}"
        if author:
            key += f"|{author.lower().strip()}"
        return key

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if not expired"""
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        import time
        if time.time() - cached_item['timestamp'] > self.cache_duration:
            # Cache expired, remove it
            del self._cache[cache_key]
            return None
        
        return cached_item['data']

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save data to cache with timestamp"""
        import time
        self._cache[cache_key] = {
            'data': data.copy(),
            'timestamp': time.time()
        }
        
        # Simple cache cleanup - remove oldest entries if cache gets too large
        if len(self._cache) > 1000:  # Max 1000 cached items
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]


# Global instance
book_details_service = BookDetailsService()