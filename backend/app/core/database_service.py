"""
Unified database service layer supporting both SQLite and PostgreSQL
"""
import logging
import os
from contextlib import contextmanager
from typing import Optional, Any, Dict, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .database import get_db_connection, get_db_cursor  # SQLite functions
from ..db.database import Base, get_db  # SQLAlchemy setup

logger = logging.getLogger(__name__)


class DatabaseService:
    """Unified database service supporting both SQLite and SQLAlchemy/PostgreSQL"""
    
    def __init__(self):
        self.settings = get_settings()
        self.use_sqlite = not (
            self.settings.USE_POSTGRESQL or 
            os.getenv("RAILWAY_PROJECT_ID") or 
            "postgresql://" in self.settings.DATABASE_URL
        )
        
        if not self.use_sqlite:
            # Initialize SQLAlchemy engine for PostgreSQL
            self.engine = create_engine(
                self.settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # Set to True for SQL logging
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info(f"🐘 Database service initialized with PostgreSQL: {self.settings.DATABASE_URL}")
        else:
            self.engine = None
            self.SessionLocal = None
            logger.info(f"🗄️ Database service initialized with SQLite: {self.settings.DB_PATH}")
    
    @contextmanager
    def get_session(self):
        """Get database session - works with both SQLite and PostgreSQL"""
        if self.use_sqlite:
            # Use existing SQLite connection pattern
            with get_db_cursor() as (cursor, conn):
                yield SQLiteSession(cursor, conn)
        else:
            # Use SQLAlchemy session
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                session.close()
    
    def create_tables(self):
        """Create database tables"""
        if self.use_sqlite:
            from .database import init_database
            init_database()
        else:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ PostgreSQL tables created")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if self.use_sqlite:
                conn = get_db_connection()
                conn.execute("SELECT 1")
                conn.close()
            else:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


class SQLiteSession:
    """Wrapper to make SQLite cursor work like SQLAlchemy session"""
    
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection
    
    def execute(self, query: str, params: tuple = None):
        """Execute a query"""
        if params:
            return self.cursor.execute(query, params)
        else:
            return self.cursor.execute(query)
    
    def fetchone(self):
        """Fetch one result"""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all results"""
        return self.cursor.fetchall()
    
    def commit(self):
        """Commit transaction"""
        self.connection.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.connection.rollback()


# Global database service instance
db_service = DatabaseService()


@contextmanager
def get_db_session():
    """Global function to get database session"""
    with db_service.get_session() as session:
        yield session


def init_db():
    """Initialize database tables"""
    db_service.create_tables()


def test_db_connection() -> bool:
    """Test database connection"""
    return db_service.test_connection()