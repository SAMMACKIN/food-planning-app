from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ReadingStatus(str, Enum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"


class BookBase(BaseModel):
    title: str = Field(..., max_length=500)
    author: str = Field(..., max_length=300)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    isbn: Optional[str] = Field(None, max_length=20)
    pages: Optional[int] = Field(None, ge=0)
    publication_year: Optional[int] = Field(None, ge=0, le=3000)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    google_books_id: Optional[str] = Field(None, max_length=100)
    open_library_id: Optional[str] = Field(None, max_length=100)


class BookCreate(BookBase):
    current_page: Optional[int] = Field(0, ge=0)
    reading_status: ReadingStatus = ReadingStatus.WANT_TO_READ
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = False
    source: Optional[str] = Field("user_added", max_length=100)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    isbn: Optional[str] = Field(None, max_length=20)
    pages: Optional[int] = Field(None, ge=0)
    publication_year: Optional[int] = Field(None, ge=0, le=3000)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    google_books_id: Optional[str] = Field(None, max_length=100)
    open_library_id: Optional[str] = Field(None, max_length=100)
    current_page: Optional[int] = Field(None, ge=0)
    reading_status: Optional[ReadingStatus] = None
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=100)


class BookResponse(BookBase):
    id: str
    user_id: str
    current_page: int
    reading_status: ReadingStatus
    date_started: Optional[datetime]
    date_finished: Optional[datetime]
    user_notes: Optional[str]
    is_favorite: bool
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    books: List[BookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BookFilters(BaseModel):
    reading_status: Optional[ReadingStatus] = None
    genre: Optional[str] = None
    is_favorite: Optional[bool] = None
    search: Optional[str] = None  # Search in title, author, or description


class BookDetailsRequest(BaseModel):
    title: str = Field(..., max_length=500)
    author: Optional[str] = Field(None, max_length=300)


class BookDetailsConfidence(BaseModel):
    publication_year: Optional[float] = Field(None, ge=0.0, le=1.0)
    pages: Optional[float] = Field(None, ge=0.0, le=1.0)
    genre: Optional[float] = Field(None, ge=0.0, le=1.0)
    description: Optional[float] = Field(None, ge=0.0, le=1.0)
    isbn: Optional[float] = Field(None, ge=0.0, le=1.0)


class BookDetailsResponse(BaseModel):
    title: str
    author: str
    publication_year: Optional[int] = None
    pages: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    cover_image_url: Optional[str] = None
    google_books_id: Optional[str] = None
    open_library_id: Optional[str] = None
    confidence: Optional[BookDetailsConfidence] = None
    sources: List[str] = []  # e.g., ["ai", "openlibrary", "google_books"]


class BookRecommendationRequest(BaseModel):
    max_recommendations: Optional[int] = Field(5, ge=1, le=20)
    exclude_genres: Optional[List[str]] = []
    preferred_genres: Optional[List[str]] = []
    include_reasoning: Optional[bool] = True


class BookRecommendation(BaseModel):
    title: str = Field(..., max_length=500)
    author: str = Field(..., max_length=300)
    genre: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    publication_year: Optional[int] = None
    pages: Optional[int] = None
    cover_image_url: Optional[str] = None
    reasoning: Optional[str] = None  # AI explanation for this recommendation
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class BookRecommendationResponse(BaseModel):
    recommendations: List[BookRecommendation]
    session_id: str
    context_summary: str  # Summary of what influenced these recommendations
    total_recommendations: int
    
    
class FeedbackType(str, Enum):
    READ = "read"
    WANT_TO_READ = "want_to_read"
    NOT_INTERESTED = "not_interested"


class BookRecommendationFeedbackRequest(BaseModel):
    session_id: str = Field(..., max_length=100)
    recommendation_title: str = Field(..., max_length=500)
    recommendation_author: str = Field(..., max_length=300)
    feedback_type: FeedbackType
    feedback_notes: Optional[str] = None


class BookRecommendationFeedbackResponse(BaseModel):
    success: bool
    message: str
    updated_recommendations: Optional[BookRecommendationResponse] = None  # New recommendations based on feedback