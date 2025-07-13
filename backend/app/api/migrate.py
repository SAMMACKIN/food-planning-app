"""
Database migration endpoints - for Railway deployment
"""
import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from ..core.config import get_settings
from ..db.database import Base, engine as db_engine
from ..models import Book, TVShow, Movie, ContentRating, EpisodeWatch, ContentShare

router = APIRouter(tags=["migration"])
logger = logging.getLogger(__name__)


@router.post("/migrate-recipes-v2")
async def migrate_recipes_v2():
    """Migrate recipes_v2 table to new schema"""
    
    settings = get_settings()
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if recipes_v2 table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'recipes_v2'
                    );
                """))
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.info("Creating new recipes_v2 table...")
                    # Create the table from scratch
                    conn.execute(text("""
                        CREATE TABLE recipes_v2 (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES users(id),
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            prep_time INTEGER NOT NULL,
                            difficulty VARCHAR(50) NOT NULL,
                            servings INTEGER NOT NULL,
                            ingredients_needed JSON NOT NULL DEFAULT '[]',
                            instructions JSON NOT NULL DEFAULT '[]',
                            tags JSON NOT NULL DEFAULT '[]',
                            nutrition_notes TEXT DEFAULT '',
                            pantry_usage_score INTEGER DEFAULT 0,
                            source VARCHAR(100) DEFAULT 'user_created',
                            ai_generated BOOLEAN DEFAULT FALSE,
                            ai_provider VARCHAR(50),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """))
                    message = "Created new recipes_v2 table with correct schema"
                else:
                    # Check if ingredients_needed column exists
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'recipes_v2' 
                            AND column_name = 'ingredients_needed'
                        );
                    """))
                    column_exists = result.scalar()
                    
                    if not column_exists:
                        logger.info("Updating existing recipes_v2 table schema...")
                        
                        # Drop the old table and recreate (safer than ALTER for major schema changes)
                        conn.execute(text("DROP TABLE IF EXISTS recipes_v2 CASCADE;"))
                        
                        # Create the new table
                        conn.execute(text("""
                            CREATE TABLE recipes_v2 (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                user_id UUID NOT NULL REFERENCES users(id),
                                name VARCHAR(255) NOT NULL,
                                description TEXT,
                                prep_time INTEGER NOT NULL,
                                difficulty VARCHAR(50) NOT NULL,
                                servings INTEGER NOT NULL,
                                ingredients_needed JSON NOT NULL DEFAULT '[]',
                                instructions JSON NOT NULL DEFAULT '[]',
                                tags JSON NOT NULL DEFAULT '[]',
                                nutrition_notes TEXT DEFAULT '',
                                pantry_usage_score INTEGER DEFAULT 0,
                                source VARCHAR(100) DEFAULT 'user_created',
                                ai_generated BOOLEAN DEFAULT FALSE,
                                ai_provider VARCHAR(50),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                        """))
                        message = "Recreated recipes_v2 table with new schema"
                    else:
                        message = "Schema is already up to date"
                
                # Commit the transaction
                trans.commit()
                logger.info(f"Migration completed: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "table_exists": True
                }
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Migration failed: {e}")
                raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
                
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.get("/check-recipes-v2-schema")
async def check_recipes_v2_schema():
    """Check the current recipes_v2 table schema"""
    
    settings = get_settings()
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'recipes_v2'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                return {
                    "table_exists": False,
                    "message": "recipes_v2 table does not exist"
                }
            
            # Get column information
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'recipes_v2'
                ORDER BY ordinal_position;
            """))
            columns = [
                {
                    "column_name": row[0],
                    "data_type": row[1], 
                    "is_nullable": row[2],
                    "column_default": row[3]
                }
                for row in result
            ]
            
            # Check specific columns we need
            column_names = [col['column_name'] for col in columns]
            has_ingredients_needed = 'ingredients_needed' in column_names
            has_pantry_usage_score = 'pantry_usage_score' in column_names
            
            return {
                "table_exists": True,
                "has_ingredients_needed": has_ingredients_needed,
                "has_pantry_usage_score": has_pantry_usage_score,
                "columns": columns,
                "schema_compatible": has_ingredients_needed and has_pantry_usage_score
            }
                
    except Exception as e:
        logger.error(f"Schema check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Schema check failed: {str(e)}")


@router.post("/create-content-tables")
async def create_content_tables():
    """Create all new content tables for books, TV shows, and movies"""
    try:
        # Create all tables defined in our models
        Base.metadata.create_all(bind=db_engine, tables=[
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
        
        with db_engine.connect() as conn:
            for table in tables_to_check:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    tables_created.append(table)
                except ProgrammingError:
                    pass
        
        logger.info(f"Content tables migration completed. Created: {tables_created}")
        
        return {
            "success": True,
            "message": "Content tables migration completed successfully",
            "tables_created": tables_created
        }
        
    except Exception as e:
        logger.error(f"Content tables migration failed: {e}")
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
    
    try:
        with db_engine.connect() as conn:
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
    
    except Exception as e:
        logger.error(f"Content tables verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )