"""
Add dietary_restrictions column to family_members table
"""
import logging
from sqlalchemy import create_engine, text
from ..core.config import get_settings

logger = logging.getLogger(__name__)

def add_dietary_restrictions_column():
    """Add dietary_restrictions column to family_members table if it doesn't exist"""
    try:
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if dietary_restrictions column exists
            check_column_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='family_members' 
                AND column_name='dietary_restrictions'
            """)
            
            result = conn.execute(check_column_sql)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                logger.info("Adding dietary_restrictions column to family_members table...")
                
                # Add the column with JSON type and default empty array
                add_column_sql = text("""
                    ALTER TABLE family_members 
                    ADD COLUMN dietary_restrictions JSON DEFAULT '[]'::json
                """)
                
                conn.execute(add_column_sql)
                conn.commit()
                
                logger.info("✅ Successfully added dietary_restrictions column")
            else:
                logger.info("✅ dietary_restrictions column already exists")
                
    except Exception as e:
        logger.error(f"❌ Failed to add dietary_restrictions column: {e}")
        raise