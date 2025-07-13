#!/usr/bin/env python3
"""
Migration script to create new content tables for books, TV shows, and movies
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check if we're on Railway by looking for environment variables
is_railway = bool(os.getenv('RAILWAY_PUBLIC_DOMAIN') or os.getenv('RAILWAY_PROJECT_ID'))

if is_railway:
    # Running on Railway - use the configured database
    from app.db.database import engine
    print("Running on Railway - using configured database")
else:
    # Running locally - need to use Railway database URL
    print("Running locally - this script should be run on Railway deployment")
    print("Please deploy to preview and run the migration there, or set up local PostgreSQL")
    sys.exit(1)

from app.db.database import Base
from app.models import Book, TVShow, Movie, ContentRating, EpisodeWatch, ContentShare


def create_content_tables():
    """Create all new content tables"""
    
    print("Creating content tables...")
    
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
        
        print("✅ Successfully created content tables:")
        print("  - books")
        print("  - tv_shows") 
        print("  - movies")
        print("  - content_ratings")
        print("  - episode_watches")
        print("  - content_shares")
        
    except Exception as e:
        print(f"❌ Error creating content tables: {e}")
        return False
    
    return True


def verify_tables():
    """Verify that all tables were created successfully"""
    
    tables_to_check = [
        'books', 'tv_shows', 'movies', 
        'content_ratings', 'episode_watches', 'content_shares'
    ]
    
    print("\nVerifying table creation...")
    
    with engine.connect() as conn:
        for table in tables_to_check:
            try:
                result = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                print(f"✅ Table '{table}' exists and is accessible")
            except ProgrammingError:
                print(f"❌ Table '{table}' does not exist or is not accessible")
                return False
    
    return True


if __name__ == "__main__":
    print("Content Tables Migration Script")
    print("=" * 50)
    
    # Create the tables
    success = create_content_tables()
    
    if success:
        # Verify tables were created
        verify_success = verify_tables()
        
        if verify_success:
            print("\n🎉 Content tables migration completed successfully!")
            print("The application now supports books, TV shows, and movies.")
        else:
            print("\n⚠️ Tables were created but verification failed.")
            sys.exit(1)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)