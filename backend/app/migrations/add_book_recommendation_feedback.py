"""
Migration to add book_recommendation_feedback table for AI learning system
"""
import logging
import sys
import os

# Add the project root to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import SessionLocal
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def add_book_recommendation_feedback_table():
    """
    Add the book_recommendation_feedback table to track user feedback on AI recommendations
    """
    db = SessionLocal()
    try:
        logger.info("🔄 Checking for book_recommendation_feedback table...")
        
        # Check if table already exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'book_recommendation_feedback'
            );
        """))
        table_exists = result.scalar()
        
        if table_exists:
            logger.info("✅ book_recommendation_feedback table already exists")
            return
        
        logger.info("📝 Creating book_recommendation_feedback table...")
        
        # Create the book_recommendation_feedback table
        db.execute(text("""
            CREATE TABLE book_recommendation_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                recommendation_session_id VARCHAR(100) NOT NULL,
                recommended_title VARCHAR(500) NOT NULL,
                recommended_author VARCHAR(300) NOT NULL,
                recommended_genre VARCHAR(100),
                recommended_description TEXT,
                ai_reasoning TEXT,
                feedback_type VARCHAR(50) NOT NULL,
                feedback_notes TEXT,
                context_books JSON DEFAULT '[]'::json,
                context_genres JSON DEFAULT '[]'::json,
                context_feedback_history JSON DEFAULT '{}'::json,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """))
        
        # Create indexes for better query performance
        db.execute(text("""
            CREATE INDEX idx_book_recommendation_feedback_user_id 
            ON book_recommendation_feedback(user_id);
        """))
        
        db.execute(text("""
            CREATE INDEX idx_book_recommendation_feedback_session_id 
            ON book_recommendation_feedback(recommendation_session_id);
        """))
        
        db.execute(text("""
            CREATE INDEX idx_book_recommendation_feedback_type 
            ON book_recommendation_feedback(feedback_type);
        """))
        
        db.execute(text("""
            CREATE INDEX idx_book_recommendation_feedback_created_at 
            ON book_recommendation_feedback(created_at);
        """))
        
        # Add trigger to update updated_at column
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_book_recommendation_feedback_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        db.execute(text("""
            CREATE TRIGGER update_book_recommendation_feedback_updated_at
                BEFORE UPDATE ON book_recommendation_feedback
                FOR EACH ROW
                EXECUTE FUNCTION update_book_recommendation_feedback_updated_at();
        """))
        
        db.commit()
        logger.info("✅ Successfully created book_recommendation_feedback table with indexes and triggers")
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error creating book_recommendation_feedback table: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating book_recommendation_feedback table: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_book_recommendation_feedback_table()