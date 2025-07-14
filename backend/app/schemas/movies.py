from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ViewingStatus(str, Enum):
    WANT_TO_WATCH = "want_to_watch"
    WATCHED = "watched"


class MovieBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    director: Optional[str] = Field(None, max_length=200)
    release_year: Optional[int] = Field(None, ge=1900, le=3000)
    runtime: Optional[int] = Field(None, ge=0)  # minutes
    poster_image_url: Optional[str] = Field(None, max_length=500)
    tmdb_id: Optional[str] = Field(None, max_length=100)
    imdb_id: Optional[str] = Field(None, max_length=100)
    omdb_id: Optional[str] = Field(None, max_length=100)


class MovieCreate(MovieBase):
    viewing_status: ViewingStatus = ViewingStatus.WANT_TO_WATCH
    date_watched: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = False
    source: Optional[str] = Field("user_added", max_length=100)


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    director: Optional[str] = Field(None, max_length=200)
    release_year: Optional[int] = Field(None, ge=1900, le=3000)
    runtime: Optional[int] = Field(None, ge=0)
    poster_image_url: Optional[str] = Field(None, max_length=500)
    tmdb_id: Optional[str] = Field(None, max_length=100)
    imdb_id: Optional[str] = Field(None, max_length=100)
    omdb_id: Optional[str] = Field(None, max_length=100)
    viewing_status: Optional[ViewingStatus] = None
    date_watched: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=100)


class MovieResponse(MovieBase):
    id: str
    user_id: str
    viewing_status: ViewingStatus
    date_watched: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: bool
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MovieListResponse(BaseModel):
    movies: List[MovieResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MovieFilters(BaseModel):
    viewing_status: Optional[ViewingStatus] = None
    genre: Optional[str] = None
    is_favorite: Optional[bool] = None
    search: Optional[str] = None


# Movie details fetching schemas
class MovieDetailsRequest(BaseModel):
    title: str = Field(..., max_length=500)
    director: Optional[str] = Field(None, max_length=200)
    release_year: Optional[int] = Field(None, ge=1900, le=3000)


class MovieDetailsResponse(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    director: Optional[str] = None
    release_year: Optional[int] = None
    runtime: Optional[int] = None
    poster_image_url: Optional[str] = None
    tmdb_id: Optional[str] = None
    imdb_id: Optional[str] = None
    omdb_id: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = []