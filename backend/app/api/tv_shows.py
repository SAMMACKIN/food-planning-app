"""
TV Shows API - Content management for TV show collection and episode tracking
"""
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from datetime import datetime

from ..db.database import get_db
from ..core.auth_service import AuthService
from ..models.content import TVShow, EpisodeWatch
from ..schemas.tv_shows import (
    TVShowCreate, TVShowUpdate, TVShowResponse, TVShowListResponse, TVShowFilters, ViewingStatus,
    EpisodeWatchCreate, EpisodeWatchUpdate, EpisodeWatchResponse, EpisodeWatchListResponse,
    WatchProgressResponse, ProgressUpdateRequest,
    TVShowDetailsRequest, TVShowDetailsResponse
)

router = APIRouter(tags=["tv_shows"])
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


@router.post("", response_model=TVShowResponse)
def create_tv_show(
    tv_show_data: TVShowCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Add a new TV show to user's collection"""
    try:
        logger.info(f"📺 Adding TV show: {tv_show_data.title} ({tv_show_data.network or 'Unknown network'})")
        
        user_uuid = uuid.UUID(current_user["id"])
        
        # Create TV show
        tv_show = TVShow(
            user_id=user_uuid,
            title=tv_show_data.title,
            description=tv_show_data.description,
            genre=tv_show_data.genre,
            network=tv_show_data.network,
            total_seasons=tv_show_data.total_seasons,
            total_episodes=tv_show_data.total_episodes,
            status=tv_show_data.status,
            first_air_date=tv_show_data.first_air_date,
            last_air_date=tv_show_data.last_air_date,
            poster_image_url=tv_show_data.poster_image_url,
            tmdb_id=tv_show_data.tmdb_id,
            tvmaze_id=tv_show_data.tvmaze_id,
            imdb_id=tv_show_data.imdb_id,
            viewing_status=tv_show_data.viewing_status,
            current_season=tv_show_data.current_season,
            current_episode=tv_show_data.current_episode,
            episodes_watched=tv_show_data.episodes_watched,
            date_started=tv_show_data.date_started,
            date_finished=tv_show_data.date_finished,
            user_notes=tv_show_data.user_notes,
            is_favorite=tv_show_data.is_favorite,
            source=tv_show_data.source
        )
        
        db.add(tv_show)
        db.commit()
        db.refresh(tv_show)
        
        logger.info(f"✅ TV show added: {tv_show.id} - {tv_show.title}")
        
        return TVShowResponse(
            id=str(tv_show.id),
            user_id=str(tv_show.user_id),
            title=tv_show.title,
            description=tv_show.description,
            genre=tv_show.genre,
            network=tv_show.network,
            total_seasons=tv_show.total_seasons,
            total_episodes=tv_show.total_episodes,
            status=tv_show.status,
            first_air_date=tv_show.first_air_date,
            last_air_date=tv_show.last_air_date,
            poster_image_url=tv_show.poster_image_url,
            tmdb_id=tv_show.tmdb_id,
            tvmaze_id=tv_show.tvmaze_id,
            imdb_id=tv_show.imdb_id,
            viewing_status=tv_show.viewing_status,
            current_season=tv_show.current_season,
            current_episode=tv_show.current_episode,
            episodes_watched=tv_show.episodes_watched,
            date_started=tv_show.date_started,
            date_finished=tv_show.date_finished,
            user_notes=tv_show.user_notes,
            is_favorite=tv_show.is_favorite,
            source=tv_show.source,
            created_at=tv_show.created_at,
            updated_at=tv_show.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Add TV show error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add TV show: {str(e)}")


@router.get("", response_model=TVShowListResponse)
def list_tv_shows(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    viewing_status: Optional[ViewingStatus] = Query(None),
    genre: Optional[str] = Query(None),
    network: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get user's TV show collection with filtering and pagination"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        logger.info(f"📺 Fetching TV shows for user: {user_uuid}")
        
        # Build query
        query = db.query(TVShow).filter(TVShow.user_id == user_uuid)
        
        # Apply filters
        if viewing_status:
            query = query.filter(TVShow.viewing_status == viewing_status)
        
        if genre:
            query = query.filter(TVShow.genre.ilike(f"%{genre}%"))
            
        if network:
            query = query.filter(TVShow.network.ilike(f"%{network}%"))
            
        if is_favorite is not None:
            query = query.filter(TVShow.is_favorite == is_favorite)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    TVShow.title.ilike(search_term),
                    TVShow.network.ilike(search_term),
                    TVShow.description.ilike(search_term),
                    TVShow.genre.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        tv_shows = query.order_by(desc(TVShow.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"📺 Found {len(tv_shows)} TV shows (page {page}/{total_pages}, total: {total})")
        
        # Convert to response format
        tv_show_responses = [
            TVShowResponse(
                id=str(tv_show.id),
                user_id=str(tv_show.user_id),
                title=tv_show.title,
                description=tv_show.description,
                genre=tv_show.genre,
                network=tv_show.network,
                total_seasons=tv_show.total_seasons,
                total_episodes=tv_show.total_episodes,
                status=tv_show.status,
                first_air_date=tv_show.first_air_date,
                last_air_date=tv_show.last_air_date,
                poster_image_url=tv_show.poster_image_url,
                tmdb_id=tv_show.tmdb_id,
                tvmaze_id=tv_show.tvmaze_id,
                imdb_id=tv_show.imdb_id,
                viewing_status=tv_show.viewing_status,
                current_season=tv_show.current_season,
                current_episode=tv_show.current_episode,
                episodes_watched=tv_show.episodes_watched,
                date_started=tv_show.date_started,
                date_finished=tv_show.date_finished,
                user_notes=tv_show.user_notes,
                is_favorite=tv_show.is_favorite,
                source=tv_show.source,
                created_at=tv_show.created_at,
                updated_at=tv_show.updated_at
            )
            for tv_show in tv_shows
        ]
        
        return TVShowListResponse(
            tv_shows=tv_show_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ List TV shows error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list TV shows: {str(e)}")


@router.get("/{tv_show_id}", response_model=TVShowResponse)
def get_tv_show(
    tv_show_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get a specific TV show by ID"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        return TVShowResponse(
            id=str(tv_show.id),
            user_id=str(tv_show.user_id),
            title=tv_show.title,
            description=tv_show.description,
            genre=tv_show.genre,
            network=tv_show.network,
            total_seasons=tv_show.total_seasons,
            total_episodes=tv_show.total_episodes,
            status=tv_show.status,
            first_air_date=tv_show.first_air_date,
            last_air_date=tv_show.last_air_date,
            poster_image_url=tv_show.poster_image_url,
            tmdb_id=tv_show.tmdb_id,
            tvmaze_id=tv_show.tvmaze_id,
            imdb_id=tv_show.imdb_id,
            viewing_status=tv_show.viewing_status,
            current_season=tv_show.current_season,
            current_episode=tv_show.current_episode,
            episodes_watched=tv_show.episodes_watched,
            date_started=tv_show.date_started,
            date_finished=tv_show.date_finished,
            user_notes=tv_show.user_notes,
            is_favorite=tv_show.is_favorite,
            source=tv_show.source,
            created_at=tv_show.created_at,
            updated_at=tv_show.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get TV show error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get TV show: {str(e)}")


@router.put("/{tv_show_id}", response_model=TVShowResponse)
def update_tv_show(
    tv_show_id: str,
    tv_show_data: TVShowUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update a TV show in user's collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Update fields
        update_data = tv_show_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tv_show, field, value)
        
        db.commit()
        db.refresh(tv_show)
        
        logger.info(f"✏️ TV show updated: {tv_show_uuid} - {tv_show.title}")
        
        return TVShowResponse(
            id=str(tv_show.id),
            user_id=str(tv_show.user_id),
            title=tv_show.title,
            description=tv_show.description,
            genre=tv_show.genre,
            network=tv_show.network,
            total_seasons=tv_show.total_seasons,
            total_episodes=tv_show.total_episodes,
            status=tv_show.status,
            first_air_date=tv_show.first_air_date,
            last_air_date=tv_show.last_air_date,
            poster_image_url=tv_show.poster_image_url,
            tmdb_id=tv_show.tmdb_id,
            tvmaze_id=tv_show.tvmaze_id,
            imdb_id=tv_show.imdb_id,
            viewing_status=tv_show.viewing_status,
            current_season=tv_show.current_season,
            current_episode=tv_show.current_episode,
            episodes_watched=tv_show.episodes_watched,
            date_started=tv_show.date_started,
            date_finished=tv_show.date_finished,
            user_notes=tv_show.user_notes,
            is_favorite=tv_show.is_favorite,
            source=tv_show.source,
            created_at=tv_show.created_at,
            updated_at=tv_show.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update TV show error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update TV show: {str(e)}")


@router.delete("/{tv_show_id}")
def delete_tv_show(
    tv_show_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Delete a TV show from collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_id,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        db.delete(tv_show)
        db.commit()
        
        logger.info(f"✅ TV show deleted: {tv_show_id}")
        
        return {"message": "TV show deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete TV show error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete TV show: {str(e)}")


@router.patch("/{tv_show_id}/viewing-status")
def update_viewing_status(
    tv_show_id: str,
    viewing_status: ViewingStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update viewing status for a TV show"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Update viewing status
        tv_show.viewing_status = viewing_status
        
        # Auto-update dates based on status
        if viewing_status == ViewingStatus.WATCHING and not tv_show.date_started:
            tv_show.date_started = datetime.utcnow()
        elif viewing_status == ViewingStatus.COMPLETED and not tv_show.date_finished:
            tv_show.date_finished = datetime.utcnow()
        elif viewing_status == ViewingStatus.WANT_TO_WATCH:
            tv_show.date_started = None
            tv_show.date_finished = None
        
        db.commit()
        
        logger.info(f"📺 Viewing status updated: {tv_show.title} - {viewing_status}")
        
        return {
            "message": "Viewing status updated",
            "viewing_status": viewing_status,
            "date_started": tv_show.date_started,
            "date_finished": tv_show.date_finished
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update viewing status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update viewing status: {str(e)}")


# Episode tracking endpoints
@router.get("/{tv_show_id}/episodes", response_model=EpisodeWatchListResponse)
def get_episodes(
    tv_show_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple),
    season: Optional[int] = Query(None, ge=1),
    watched: Optional[bool] = Query(None)
):
    """Get episodes for a TV show with optional filtering"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        # Verify TV show belongs to user
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Build episode query
        query = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == tv_show_uuid,
            EpisodeWatch.user_id == user_uuid
        )
        
        if season:
            query = query.filter(EpisodeWatch.season_number == season)
        
        if watched is not None:
            query = query.filter(EpisodeWatch.watched == watched)
        
        episodes = query.order_by(EpisodeWatch.season_number, EpisodeWatch.episode_number).all()
        
        episode_responses = [
            EpisodeWatchResponse(
                id=str(episode.id),
                tv_show_id=str(episode.tv_show_id),
                user_id=str(episode.user_id),
                season_number=episode.season_number,
                episode_number=episode.episode_number,
                episode_title=episode.episode_title,
                watched=episode.watched,
                watch_date=episode.watch_date,
                created_at=episode.created_at,
                updated_at=episode.updated_at
            )
            for episode in episodes
        ]
        
        return EpisodeWatchListResponse(
            episodes=episode_responses,
            total=len(episode_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get episodes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get episodes: {str(e)}")


@router.post("/{tv_show_id}/episodes", response_model=EpisodeWatchResponse)
def mark_episode(
    tv_show_id: str,
    episode_data: EpisodeWatchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Mark an episode as watched/unwatched"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        # Verify TV show belongs to user
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Check if episode watch record already exists
        existing_episode = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == tv_show_uuid,
            EpisodeWatch.user_id == user_uuid,
            EpisodeWatch.season_number == episode_data.season_number,
            EpisodeWatch.episode_number == episode_data.episode_number
        ).first()
        
        if existing_episode:
            # Update existing record
            existing_episode.watched = episode_data.watched
            existing_episode.watch_date = episode_data.watch_date or (datetime.utcnow() if episode_data.watched else None)
            existing_episode.episode_title = episode_data.episode_title
            db.commit()
            db.refresh(existing_episode)
            
            episode_watch = existing_episode
        else:
            # Create new record
            episode_watch = EpisodeWatch(
                tv_show_id=tv_show_uuid,
                user_id=user_uuid,
                season_number=episode_data.season_number,
                episode_number=episode_data.episode_number,
                episode_title=episode_data.episode_title,
                watched=episode_data.watched,
                watch_date=episode_data.watch_date or (datetime.utcnow() if episode_data.watched else None)
            )
            
            db.add(episode_watch)
            db.commit()
            db.refresh(episode_watch)
        
        # Update TV show progress
        watched_count = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == tv_show_uuid,
            EpisodeWatch.user_id == user_uuid,
            EpisodeWatch.watched == True
        ).count()
        
        tv_show.episodes_watched = watched_count
        
        # Find current position (latest watched episode)
        latest_watched = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == tv_show_uuid,
            EpisodeWatch.user_id == user_uuid,
            EpisodeWatch.watched == True
        ).order_by(desc(EpisodeWatch.season_number), desc(EpisodeWatch.episode_number)).first()
        
        if latest_watched:
            tv_show.current_season = latest_watched.season_number
            tv_show.current_episode = latest_watched.episode_number + 1  # Next episode
        
        db.commit()
        
        logger.info(f"📺 Episode marked: S{episode_data.season_number}E{episode_data.episode_number} - {episode_data.watched}")
        
        return EpisodeWatchResponse(
            id=str(episode_watch.id),
            tv_show_id=str(episode_watch.tv_show_id),
            user_id=str(episode_watch.user_id),
            season_number=episode_watch.season_number,
            episode_number=episode_watch.episode_number,
            episode_title=episode_watch.episode_title,
            watched=episode_watch.watched,
            watch_date=episode_watch.watch_date,
            created_at=episode_watch.created_at,
            updated_at=episode_watch.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Mark episode error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark episode: {str(e)}")


@router.get("/{tv_show_id}/progress", response_model=WatchProgressResponse)
def get_watch_progress(
    tv_show_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get watching progress for a TV show"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_uuid,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Get last watched episode date
        last_watched = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == tv_show_uuid,
            EpisodeWatch.user_id == user_uuid,
            EpisodeWatch.watched == True
        ).order_by(desc(EpisodeWatch.watch_date)).first()
        
        # Calculate completion percentage
        completion_percentage = None
        if tv_show.total_episodes and tv_show.total_episodes > 0:
            completion_percentage = (tv_show.episodes_watched / tv_show.total_episodes) * 100
        
        return WatchProgressResponse(
            tv_show_id=str(tv_show.id),
            tv_show_title=tv_show.title,
            current_season=tv_show.current_season,
            current_episode=tv_show.current_episode,
            episodes_watched=tv_show.episodes_watched,
            total_episodes=tv_show.total_episodes,
            completion_percentage=completion_percentage,
            viewing_status=tv_show.viewing_status,
            last_watched_date=last_watched.watch_date if last_watched else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get watch progress error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get watch progress: {str(e)}")


@router.patch("/{tv_show_id}/progress")
def update_progress(
    tv_show_id: str,
    progress_data: ProgressUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update watching progress by marking an episode"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        tv_show_uuid = uuid.UUID(tv_show_id)
        
        # Create episode watch entry
        episode_data = EpisodeWatchCreate(
            season_number=progress_data.season_number,
            episode_number=progress_data.episode_number,
            watched=progress_data.mark_watched,
            watch_date=datetime.utcnow() if progress_data.mark_watched else None
        )
        
        # Use the mark_episode function
        episode_response = mark_episode(tv_show_id, episode_data, db, current_user)
        
        return {
            "message": "Progress updated successfully",
            "episode": episode_response,
            "season": progress_data.season_number,
            "episode_number": progress_data.episode_number,
            "watched": progress_data.mark_watched
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update progress error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.post("/{tv_show_id}/episodes/bulk")
def bulk_mark_episodes(
    tv_show_id: str,
    season_number: int = Body(...),
    episodes: List[int] = Body(...),
    watched: bool = Body(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Bulk mark episodes as watched/unwatched"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        # Verify TV show exists
        tv_show = db.query(TVShow).filter(
            TVShow.id == tv_show_id,
            TVShow.user_id == user_uuid
        ).first()
        
        if not tv_show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Process each episode
        for episode_number in episodes:
            existing = db.query(EpisodeWatch).filter(
                EpisodeWatch.tv_show_id == tv_show_id,
                EpisodeWatch.user_id == user_uuid,
                EpisodeWatch.season_number == season_number,
                EpisodeWatch.episode_number == episode_number
            ).first()
            
            if existing:
                existing.watched = watched
                existing.watch_date = datetime.utcnow() if watched else None
            else:
                episode_watch = EpisodeWatch(
                    user_id=user_uuid,
                    tv_show_id=uuid.UUID(tv_show_id),
                    season_number=season_number,
                    episode_number=episode_number,
                    watched=watched,
                    watch_date=datetime.utcnow() if watched else None
                )
                db.add(episode_watch)
        
        # Update TV show progress
        tv_show.episodes_watched = db.query(EpisodeWatch).filter(
            EpisodeWatch.tv_show_id == uuid.UUID(tv_show_id),
            EpisodeWatch.user_id == user_uuid,
            EpisodeWatch.watched == True
        ).count()
        
        db.commit()
        
        return {"message": f"Marked {len(episodes)} episodes as {'watched' if watched else 'unwatched'}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk mark episodes error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to bulk mark episodes: {str(e)}")


@router.get("/debug/health")
def tv_shows_health_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Health check endpoint for TV shows system"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        tv_show_count = db.query(TVShow).filter(TVShow.user_id == user_uuid).count()
        episode_count = db.query(EpisodeWatch).filter(EpisodeWatch.user_id == user_uuid).count()
        
        return {
            "status": "healthy",
            "service": "tv_shows",
            "user_id": str(user_uuid),
            "user_tv_show_count": tv_show_count,
            "user_episode_count": episode_count,
            "database_connected": True,
            "table_accessible": True
        }
        
    except Exception as e:
        logger.error(f"❌ TV shows health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "tv_shows",
            "error": str(e),
            "database_connected": False,
            "table_accessible": False
        }


@router.post("/fetch-details", response_model=TVShowDetailsResponse)
async def fetch_tv_show_details(
    request: TVShowDetailsRequest,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Fetch TV show details using external APIs (TMDB, TVMaze, etc.)
    
    This endpoint accepts a TV show title and optional network/year,
    then uses external APIs to fetch comprehensive show information
    including description, genre, episode counts, poster, and external IDs.
    """
    try:
        logger.info(f"📺 Fetching TV show details for: {request.title} ({request.network or 'Unknown network'})")
        
        # TODO: Implement TV show details service similar to movie_details_service
        # For now, return a basic response
        
        response = TVShowDetailsResponse(
            title=request.title,
            network=request.network,
            first_air_date=None if not request.first_air_year else datetime(request.first_air_year, 1, 1),
            confidence=0.5,
            sources=["manual_entry"]
        )
        
        logger.info(f"✅ TV show details response prepared for: {request.title}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fetch TV show details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch TV show details: {str(e)}")