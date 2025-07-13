"""
Migration endpoints for database operations
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.database import get_db, engine, Base
from app.models import Book, TVShow, Movie, ContentRating, EpisodeWatch, ContentShare

router = APIRouter()


@router.post("/create-content-tables")
async def create_content_tables():
    """Create all new content tables for books, TV shows, and movies"""
    try:
        # Create all tables defined in our models
        Base.metadata.create_all(bind=engine, tables=[
            Book.__table__,
            TVShow.__table__,
            Movie.__table__,
            ContentRating.__table__,
            EpisodeWatch.__table__,
            ContentShare.__table__
        ])
        
        # Verify tables were created
        tables_created = []
        tables_to_check = [
            'books', 'tv_shows', 'movies', 
            'content_ratings', 'episode_watches', 'content_shares'
        ]
        
        with engine.connect() as conn:
            for table in tables_to_check:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    tables_created.append(table)
                except ProgrammingError:
                    pass
        
        return {
            "success": True,
            "message": "Content tables migration completed successfully",
            "tables_created": tables_created
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/verify-content-tables")
async def verify_content_tables():
    """Verify that all content tables exist"""
    tables_to_check = [
        'books', 'tv_shows', 'movies', 
        'content_ratings', 'episode_watches', 'content_shares'
    ]
    
    existing_tables = []
    missing_tables = []
    
    with engine.connect() as conn:
        for table in tables_to_check:
            try:
                conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                existing_tables.append(table)
            except ProgrammingError:
                missing_tables.append(table)
    
    return {
        "existing_tables": existing_tables,
        "missing_tables": missing_tables,
        "all_tables_exist": len(missing_tables) == 0
    }