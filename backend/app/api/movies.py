"""
Movies API - Content management for movie collection
"""
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from ..db.database import get_db
from ..core.auth_service import AuthService
from ..models.content import Movie
from ..schemas.movies import (
    MovieCreate, MovieUpdate, MovieResponse, MovieListResponse, MovieFilters, ViewingStatus,
    MovieDetailsRequest, MovieDetailsResponse
)
from ..services.netflix_import_service import netflix_import_service
from fastapi.responses import JSONResponse

router = APIRouter(tags=["movies"])
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


@router.post("", response_model=MovieResponse)
def create_movie(
    movie_data: MovieCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Add a new movie to user's collection"""
    try:
        logger.info(f"🎬 Adding movie: {movie_data.title} ({movie_data.release_year or 'Unknown year'})")
        
        user_uuid = uuid.UUID(current_user["id"])
        
        # Create movie
        movie = Movie(
            user_id=user_uuid,
            title=movie_data.title,
            description=movie_data.description,
            genre=movie_data.genre,
            director=movie_data.director,
            release_year=movie_data.release_year,
            runtime=movie_data.runtime,
            poster_image_url=movie_data.poster_image_url,
            tmdb_id=movie_data.tmdb_id,
            imdb_id=movie_data.imdb_id,
            omdb_id=movie_data.omdb_id,
            viewing_status=movie_data.viewing_status,
            date_watched=movie_data.date_watched,
            user_notes=movie_data.user_notes,
            is_favorite=movie_data.is_favorite,
            source=movie_data.source
        )
        
        db.add(movie)
        db.commit()
        db.refresh(movie)
        
        logger.info(f"✅ Movie added: {movie.id} - {movie.title}")
        
        return MovieResponse(
            id=str(movie.id),
            user_id=str(movie.user_id),
            title=movie.title,
            description=movie.description,
            genre=movie.genre,
            director=movie.director,
            release_year=movie.release_year,
            runtime=movie.runtime,
            poster_image_url=movie.poster_image_url,
            tmdb_id=movie.tmdb_id,
            imdb_id=movie.imdb_id,
            omdb_id=movie.omdb_id,
            viewing_status=movie.viewing_status,
            date_watched=movie.date_watched,
            user_notes=movie.user_notes,
            is_favorite=movie.is_favorite,
            source=movie.source,
            created_at=movie.created_at,
            updated_at=movie.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Add movie error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add movie: {str(e)}")


@router.get("", response_model=MovieListResponse)
def list_movies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    viewing_status: Optional[ViewingStatus] = Query(None),
    genre: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get user's movie collection with filtering and pagination"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        logger.info(f"🎬 Fetching movies for user: {user_uuid}")
        
        # Build query
        query = db.query(Movie).filter(Movie.user_id == user_uuid)
        
        # Apply filters
        if viewing_status:
            query = query.filter(Movie.viewing_status == viewing_status)
        
        if genre:
            query = query.filter(Movie.genre.ilike(f"%{genre}%"))
            
        if is_favorite is not None:
            query = query.filter(Movie.is_favorite == is_favorite)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Movie.title.ilike(search_term),
                    Movie.director.ilike(search_term),
                    Movie.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        movies = query.order_by(desc(Movie.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"🎬 Found {len(movies)} movies (page {page}/{total_pages}, total: {total})")
        
        # Convert to response format
        movie_responses = [
            MovieResponse(
                id=str(movie.id),
                user_id=str(movie.user_id),
                title=movie.title,
                description=movie.description,
                genre=movie.genre,
                director=movie.director,
                release_year=movie.release_year,
                runtime=movie.runtime,
                poster_image_url=movie.poster_image_url,
                tmdb_id=movie.tmdb_id,
                imdb_id=movie.imdb_id,
                omdb_id=movie.omdb_id,
                viewing_status=movie.viewing_status,
                date_watched=movie.date_watched,
                user_notes=movie.user_notes,
                is_favorite=movie.is_favorite,
                source=movie.source,
                created_at=movie.created_at,
                updated_at=movie.updated_at
            )
            for movie in movies
        ]
        
        return MovieListResponse(
            movies=movie_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ List movies error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list movies: {str(e)}")


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Get a specific movie by ID"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        movie_uuid = uuid.UUID(movie_id)
        
        movie = db.query(Movie).filter(
            Movie.id == movie_uuid,
            Movie.user_id == user_uuid
        ).first()
        
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        return MovieResponse(
            id=str(movie.id),
            user_id=str(movie.user_id),
            title=movie.title,
            description=movie.description,
            genre=movie.genre,
            director=movie.director,
            release_year=movie.release_year,
            runtime=movie.runtime,
            poster_image_url=movie.poster_image_url,
            tmdb_id=movie.tmdb_id,
            imdb_id=movie.imdb_id,
            omdb_id=movie.omdb_id,
            viewing_status=movie.viewing_status,
            date_watched=movie.date_watched,
            user_notes=movie.user_notes,
            is_favorite=movie.is_favorite,
            source=movie.source,
            created_at=movie.created_at,
            updated_at=movie.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get movie error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get movie: {str(e)}")


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(
    movie_id: str,
    movie_data: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update a movie in user's collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        movie_uuid = uuid.UUID(movie_id)
        
        movie = db.query(Movie).filter(
            Movie.id == movie_uuid,
            Movie.user_id == user_uuid
        ).first()
        
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Update fields
        update_data = movie_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(movie, field, value)
        
        db.commit()
        db.refresh(movie)
        
        logger.info(f"✏️ Movie updated: {movie_uuid} - {movie.title}")
        
        return MovieResponse(
            id=str(movie.id),
            user_id=str(movie.user_id),
            title=movie.title,
            description=movie.description,
            genre=movie.genre,
            director=movie.director,
            release_year=movie.release_year,
            runtime=movie.runtime,
            poster_image_url=movie.poster_image_url,
            tmdb_id=movie.tmdb_id,
            imdb_id=movie.imdb_id,
            omdb_id=movie.omdb_id,
            viewing_status=movie.viewing_status,
            date_watched=movie.date_watched,
            user_notes=movie.user_notes,
            is_favorite=movie.is_favorite,
            source=movie.source,
            created_at=movie.created_at,
            updated_at=movie.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update movie error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update movie: {str(e)}")


@router.delete("/{movie_id}")
def delete_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Remove a movie from user's collection"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        movie_uuid = uuid.UUID(movie_id)
        
        movie = db.query(Movie).filter(
            Movie.id == movie_uuid,
            Movie.user_id == user_uuid
        ).first()
        
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        db.delete(movie)
        db.commit()
        
        logger.info(f"🗑️ Movie deleted: {movie_uuid} - {movie.title}")
        return {"message": "Movie deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete movie error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete movie: {str(e)}")


@router.patch("/{movie_id}/viewing-status")
def update_viewing_status(
    movie_id: str,
    viewing_status: ViewingStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Update viewing status for a movie"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        movie_uuid = uuid.UUID(movie_id)
        
        movie = db.query(Movie).filter(
            Movie.id == movie_uuid,
            Movie.user_id == user_uuid
        ).first()
        
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Update viewing status
        movie.viewing_status = viewing_status
        
        # Auto-update date_watched based on status
        if viewing_status == ViewingStatus.WATCHED and not movie.date_watched:
            from datetime import datetime
            movie.date_watched = datetime.utcnow()
        elif viewing_status == ViewingStatus.WANT_TO_WATCH:
            movie.date_watched = None
        
        db.commit()
        
        logger.info(f"🎬 Viewing status updated: {movie.title} - {viewing_status}")
        
        return {
            "message": "Viewing status updated",
            "viewing_status": viewing_status,
            "date_watched": movie.date_watched
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update viewing status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update viewing status: {str(e)}")


@router.get("/debug/health")
def movies_health_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """Health check endpoint for movies system"""
    try:
        user_uuid = uuid.UUID(current_user["id"])
        
        movie_count = db.query(Movie).filter(Movie.user_id == user_uuid).count()
        
        return {
            "status": "healthy",
            "service": "movies",
            "user_id": str(user_uuid),
            "user_movie_count": movie_count,
            "database_connected": True,
            "table_accessible": True
        }
        
    except Exception as e:
        logger.error(f"❌ Movies health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "movies",
            "error": str(e),
            "database_connected": False,
            "table_accessible": False
        }


@router.post("/fetch-details", response_model=MovieDetailsResponse)
async def fetch_movie_details(
    request: MovieDetailsRequest,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Fetch movie details using external APIs (TMDB, OMDB, etc.)
    
    This endpoint accepts a movie title and optional director/year,
    then uses external APIs to fetch comprehensive movie information
    including description, genre, runtime, poster, and external IDs.
    """
    try:
        logger.info(f"🎬 Fetching movie details for: {request.title} ({request.release_year or 'Unknown year'})")
        
        # TODO: Implement movie details service similar to book_details_service
        # For now, return a basic response
        
        response = MovieDetailsResponse(
            title=request.title,
            director=request.director,
            release_year=request.release_year,
            confidence=0.5,
            sources=["manual_entry"]
        )
        
        logger.info(f"✅ Movie details response prepared for: {request.title}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fetch movie details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch movie details: {str(e)}")


@router.post("/import/netflix")
async def import_netflix_history(
    file: UploadFile = File(...),
    import_movies: bool = Query(True, description="Import movies from Netflix history"),
    import_tv_shows: bool = Query(True, description="Import TV shows from Netflix history"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_simple)
):
    """
    Import viewing history from Netflix CSV export
    
    To get your Netflix viewing history:
    1. Go to Netflix.com and sign in
    2. Click on your profile icon → Account
    3. Under "Profile & Parental Controls", select your profile
    4. Click "Viewing activity"
    5. Click "Download all" at the bottom of the page
    6. Upload the downloaded CSV file here
    
    The CSV should have columns: Title, Date
    """
    try:
        logger.info(f"📺 Netflix import started for user: {current_user['id']}")
        
        # Check file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Please upload a CSV file")
        
        # Read file content
        content = await file.read()
        try:
            csv_content = content.decode('utf-8-sig')  # Handle BOM if present
        except UnicodeDecodeError:
            try:
                csv_content = content.decode('utf-8')
            except UnicodeDecodeError:
                csv_content = content.decode('latin-1')
        
        # Import using service
        result = await netflix_import_service.import_viewing_history(
            user_id=current_user["id"],
            csv_content=csv_content,
            db=db,
            import_movies=import_movies,
            import_tv_shows=import_tv_shows
        )
        
        if result['success']:
            logger.info(f"✅ Netflix import completed: {result['movies_imported']} movies, {result['tv_shows_imported']} TV shows imported")
        else:
            logger.error(f"❌ Netflix import failed: {result['message']}")
            
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Netflix import error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import Netflix history: {str(e)}")