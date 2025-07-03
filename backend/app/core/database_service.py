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
# Removed SQLite imports - now PostgreSQL only
from ..db.database import Base, get_db  # SQLAlchemy setup
from .. import models  # Import all models so Base.metadata knows about them

logger = logging.getLogger(__name__)


class DatabaseService:
    """PostgreSQL database service using SQLAlchemy"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize SQLAlchemy engine for PostgreSQL
        self.engine = create_engine(
            self.settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Set to True for SQL logging
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"🐘 Database service initialized with PostgreSQL: {self.settings.DATABASE_URL}")
    
    @contextmanager
    def get_session(self):
        """Get PostgreSQL database session"""
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
        """Create PostgreSQL database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ PostgreSQL tables created")
    
    def test_connection(self) -> bool:
        """Test PostgreSQL database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


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