"""
Unified content models for books, TV shows, movies, and recipes
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..db.database import Base


class ContentType(enum.Enum):
    """Content type enumeration"""
    RECIPE = "recipe"
    BOOK = "book"
    TV_SHOW = "tv_show"
    MOVIE = "movie"


class Book(Base):
    """
    Book model for tracking user's reading collection
    """
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic book information
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=False)
    description = Column(Text)
    genre = Column(String(100))
    isbn = Column(String(20))
    pages = Column(Integer)
    publication_year = Column(Integer)
    cover_image_url = Column(String(500))
    
    # External IDs for API integration
    google_books_id = Column(String(100))
    open_library_id = Column(String(100))
    
    # User-specific data
    current_page = Column(Integer, default=0)
    reading_status = Column(String(50), default="want_to_read")  # want_to_read, reading, read
    date_started = Column(DateTime(timezone=True))
    date_finished = Column(DateTime(timezone=True))
    user_notes = Column(Text)
    is_favorite = Column(Boolean, default=False)
    
    # Metadata
    source = Column(String(100), default="user_added")  # user_added, google_books, open_library
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="books")
    ratings = relationship("ContentRating", back_populates="book", cascade="all, delete-orphan")


class TVShow(Base):
    """
    TV Show model for tracking user's viewing collection
    """
    __tablename__ = "tv_shows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic show information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    genre = Column(String(100))
    network = Column(String(100))
    total_seasons = Column(Integer)
    total_episodes = Column(Integer)
    status = Column(String(50))  # ended, returning, canceled, running
    first_air_date = Column(DateTime(timezone=True))
    last_air_date = Column(DateTime(timezone=True))
    poster_image_url = Column(String(500))
    
    # External IDs for API integration
    tmdb_id = Column(String(100))
    tvmaze_id = Column(String(100))
    imdb_id = Column(String(100))
    
    # User-specific data
    viewing_status = Column(String(50), default="want_to_watch")  # want_to_watch, watching, completed, dropped
    current_season = Column(Integer, default=1)
    current_episode = Column(Integer, default=1)
    episodes_watched = Column(Integer, default=0)
    date_started = Column(DateTime(timezone=True))
    date_finished = Column(DateTime(timezone=True))
    user_notes = Column(Text)
    is_favorite = Column(Boolean, default=False)
    
    # Metadata
    source = Column(String(100), default="user_added")  # user_added, tmdb, tvmaze
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tv_shows")
    ratings = relationship("ContentRating", back_populates="tv_show", cascade="all, delete-orphan")
    episode_watches = relationship("EpisodeWatch", back_populates="tv_show", cascade="all, delete-orphan")


class Movie(Base):
    """
    Movie model for tracking user's movie collection
    """
    __tablename__ = "movies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic movie information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    genre = Column(String(100))
    director = Column(String(200))
    release_year = Column(Integer)
    runtime = Column(Integer)  # minutes
    poster_image_url = Column(String(500))
    
    # External IDs for API integration
    tmdb_id = Column(String(100))
    imdb_id = Column(String(100))
    omdb_id = Column(String(100))
    
    # User-specific data
    viewing_status = Column(String(50), default="want_to_watch")  # want_to_watch, watched
    date_watched = Column(DateTime(timezone=True))
    user_notes = Column(Text)
    is_favorite = Column(Boolean, default=False)
    
    # Metadata
    source = Column(String(100), default="user_added")  # user_added, tmdb, omdb
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="movies")
    ratings = relationship("ContentRating", back_populates="movie", cascade="all, delete-orphan")


class ContentRating(Base):
    """
    Unified rating system for all content types
    """
    __tablename__ = "content_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Content references (only one should be set)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes_v2.id", ondelete="CASCADE"), nullable=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=True)
    tv_show_id = Column(UUID(as_uuid=True), ForeignKey("tv_shows.id", ondelete="CASCADE"), nullable=True)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), nullable=True)
    
    # Content type for easy querying
    content_type = Column(Enum(ContentType), nullable=False)
    
    # Rating data
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text)
    
    # Content-specific fields (JSON for flexibility)
    content_specific_data = Column(JSON, default=dict)  # For content-specific rating data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    recipe = relationship("RecipeV2")
    book = relationship("Book", back_populates="ratings")
    tv_show = relationship("TVShow", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")


class EpisodeWatch(Base):
    """
    Track individual episode watches for TV shows
    """
    __tablename__ = "episode_watches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tv_show_id = Column(UUID(as_uuid=True), ForeignKey("tv_shows.id", ondelete="CASCADE"), nullable=False)
    
    # Episode identification
    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    episode_title = Column(String(300))
    
    # Watch data
    watched = Column(Boolean, default=False)
    watch_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    tv_show = relationship("TVShow", back_populates="episode_watches")


class ContentShare(Base):
    """
    Universal content sharing system
    """
    __tablename__ = "content_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Content references (only one should be set)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes_v2.id", ondelete="CASCADE"), nullable=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=True)
    tv_show_id = Column(UUID(as_uuid=True), ForeignKey("tv_shows.id", ondelete="CASCADE"), nullable=True)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), nullable=True)
    
    # Content type for easy querying
    content_type = Column(Enum(ContentType), nullable=False)
    
    # Sharing metadata
    share_message = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    recipe = relationship("RecipeV2")
    book = relationship("Book")
    tv_show = relationship("TVShow")
    movie = relationship("Movie")