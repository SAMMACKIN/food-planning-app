from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ViewingStatus(str, Enum):
    WANT_TO_WATCH = "want_to_watch"
    WATCHING = "watching"
    COMPLETED = "completed"
    DROPPED = "dropped"


class ShowStatus(str, Enum):
    ENDED = "ended"
    RETURNING = "returning"
    CANCELED = "canceled"
    RUNNING = "running"


class TVShowBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    network: Optional[str] = Field(None, max_length=100)
    total_seasons: Optional[int] = Field(None, ge=0)
    total_episodes: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)  # Show production status
    first_air_date: Optional[datetime] = None
    last_air_date: Optional[datetime] = None
    poster_image_url: Optional[str] = Field(None, max_length=500)
    tmdb_id: Optional[str] = Field(None, max_length=100)
    tvmaze_id: Optional[str] = Field(None, max_length=100)
    imdb_id: Optional[str] = Field(None, max_length=100)


class TVShowCreate(TVShowBase):
    viewing_status: ViewingStatus = ViewingStatus.WANT_TO_WATCH
    current_season: Optional[int] = Field(1, ge=1)
    current_episode: Optional[int] = Field(1, ge=1)
    episodes_watched: Optional[int] = Field(0, ge=0)
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = False
    source: Optional[str] = Field("user_added", max_length=100)


class TVShowUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    network: Optional[str] = Field(None, max_length=100)
    total_seasons: Optional[int] = Field(None, ge=0)
    total_episodes: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    first_air_date: Optional[datetime] = None
    last_air_date: Optional[datetime] = None
    poster_image_url: Optional[str] = Field(None, max_length=500)
    tmdb_id: Optional[str] = Field(None, max_length=100)
    tvmaze_id: Optional[str] = Field(None, max_length=100)
    imdb_id: Optional[str] = Field(None, max_length=100)
    viewing_status: Optional[ViewingStatus] = None
    current_season: Optional[int] = Field(None, ge=1)
    current_episode: Optional[int] = Field(None, ge=1)
    episodes_watched: Optional[int] = Field(None, ge=0)
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=100)


class TVShowResponse(TVShowBase):
    id: str
    user_id: str
    viewing_status: ViewingStatus
    current_season: int
    current_episode: int
    episodes_watched: int
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    user_notes: Optional[str] = None
    is_favorite: bool
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TVShowListResponse(BaseModel):
    tv_shows: List[TVShowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TVShowFilters(BaseModel):
    viewing_status: Optional[ViewingStatus] = None
    genre: Optional[str] = None
    network: Optional[str] = None
    is_favorite: Optional[bool] = None
    search: Optional[str] = None


# Episode tracking schemas
class EpisodeWatchBase(BaseModel):
    season_number: int = Field(..., ge=1)
    episode_number: int = Field(..., ge=1)
    episode_title: Optional[str] = Field(None, max_length=300)


class EpisodeWatchCreate(EpisodeWatchBase):
    watched: bool = True
    watch_date: Optional[datetime] = None


class EpisodeWatchUpdate(BaseModel):
    watched: Optional[bool] = None
    watch_date: Optional[datetime] = None
    episode_title: Optional[str] = Field(None, max_length=300)


class EpisodeWatchResponse(EpisodeWatchBase):
    id: str
    tv_show_id: str
    user_id: str
    watched: bool
    watch_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeWatchListResponse(BaseModel):
    episodes: List[EpisodeWatchResponse]
    total: int


# Progress tracking schemas
class WatchProgressResponse(BaseModel):
    tv_show_id: str
    tv_show_title: str
    current_season: int
    current_episode: int
    episodes_watched: int
    total_episodes: Optional[int] = None
    completion_percentage: Optional[float] = None
    viewing_status: ViewingStatus
    last_watched_date: Optional[datetime] = None


class ProgressUpdateRequest(BaseModel):
    season_number: int = Field(..., ge=1)
    episode_number: int = Field(..., ge=1)
    mark_watched: bool = True


# TV show details fetching schemas
class TVShowDetailsRequest(BaseModel):
    title: str = Field(..., max_length=500)
    network: Optional[str] = Field(None, max_length=100)
    first_air_year: Optional[int] = Field(None, ge=1900, le=3000)


class TVShowDetailsResponse(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    network: Optional[str] = None
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    status: Optional[str] = None
    first_air_date: Optional[datetime] = None
    last_air_date: Optional[datetime] = None
    poster_image_url: Optional[str] = None
    tmdb_id: Optional[str] = None
    tvmaze_id: Optional[str] = None
    imdb_id: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = []