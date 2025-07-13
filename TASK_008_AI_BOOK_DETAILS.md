# TASK_008: AI-Powered Book Details Auto-Fill

## Status: PENDING

## Overview
Implement AI-powered automatic book details fetching when users add a book by just entering the title and/or author. The system should automatically retrieve and fill in details like publication year, number of pages, genre, description, and cover image.

## Requirements

### 1. Backend AI Integration
- Create new endpoint: `POST /api/v1/books/fetch-details`
- Accept book title and optional author name
- Use AI providers to fetch book information:
  - Publication year
  - Number of pages
  - Genre classification
  - Book description/synopsis
  - ISBN (if available)
  - Cover image URL (from Open Library or Google Books API)

### 2. AI Provider Implementation
- Extend existing AI service to support book metadata queries
- Use structured prompts to get consistent book data
- Implement fallback between providers (Perplexity → Claude → Groq)
- Cache results to avoid repeated API calls for same books

### 3. External API Integration (Optional Enhancement)
- Integrate with Open Library API for cover images
- Use Google Books API as secondary source
- Implement ISBN lookup service

### 4. Frontend Integration
- Add "Auto-fill Details" button in AddBookDialog
- Show loading state while fetching
- Allow users to override AI-suggested values
- Display confidence indicators for AI-generated data

### 5. User Experience
- Make the feature optional - users can still manually enter all details
- Provide clear indication which fields were AI-filled
- Allow editing of all auto-filled fields
- Show source of information (AI-generated vs API)

## API Endpoint Design

```python
@router.post("/fetch-details")
async def fetch_book_details(
    request: BookDetailsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch book details using AI and external APIs
    
    Request body:
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald"  # optional
    }
    
    Response:
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "publication_year": 1925,
        "pages": 180,
        "genre": "Classic Literature",
        "description": "A novel set in the Jazz Age...",
        "isbn": "9780743273565",
        "cover_image_url": "https://covers.openlibrary.org/...",
        "confidence": {
            "publication_year": 0.95,
            "pages": 0.85,
            "genre": 0.90
        },
        "sources": ["ai", "openlibrary"]
    }
    """
```

## Implementation Steps

1. **Backend AI Service Extension**
   - Add book details prompt template
   - Implement structured response parsing
   - Add validation for AI responses

2. **External API Integration**
   - Create Open Library API client
   - Implement cover image fetching
   - Add rate limiting and caching

3. **Frontend UI Updates**
   - Modify AddBookDialog component
   - Add auto-fill trigger button
   - Implement loading states
   - Show confidence indicators

4. **Caching Layer**
   - Cache book details for 30 days
   - Use title + author as cache key
   - Implement cache invalidation

## Success Criteria
- Users can add books with just title/author
- AI accurately fills in missing details
- Cover images are retrieved when available
- System gracefully handles API failures
- Performance remains fast with caching

## Dependencies
- TASK_003: Books Backend API (completed)
- Existing AI service infrastructure

## Notes
- Consider rate limiting to prevent API abuse
- Implement proper error handling for external APIs
- Ensure GDPR compliance for cached data
- Add admin ability to review/correct AI-generated data