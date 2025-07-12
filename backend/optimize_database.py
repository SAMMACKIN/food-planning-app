#!/usr/bin/env python3
"""
Database optimization script to add performance indexes for saved recipes
"""
import logging
import sys
import os
from sqlalchemy import create_engine, text

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.database_service import get_db_session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def create_performance_indexes():
    """Create performance indexes for RecipeV2 table"""
    
    indexes = [
        # Critical performance indexes for RecipeV2
        {
            'name': 'idx_recipes_v2_user_id',
            'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_user_id ON recipes_v2(user_id);',
            'description': 'Primary user_id index for fast recipe lookups'
        },
        {
            'name': 'idx_recipes_v2_user_updated',
            'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_user_updated ON recipes_v2(user_id, updated_at DESC);',
            'description': 'Compound index for user_id + ordering'
        },
        # Search performance indexes
        {
            'name': 'idx_recipes_v2_name',
            'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_name ON recipes_v2(name);',
            'description': 'Recipe name search index'
        },
        {
            'name': 'idx_recipes_v2_difficulty',
            'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_difficulty ON recipes_v2(difficulty);',
            'description': 'Recipe difficulty filter index'
        }
    ]
    
    try:
        with get_db_session() as session:
            logger.info("🔧 Starting database optimization...")
            
            for index in indexes:
                try:
                    logger.info(f"📊 Creating index: {index['name']} - {index['description']}")
                    
                    # Use regular CREATE INDEX (not CONCURRENTLY) for better compatibility
                    query = index['query'].replace('CONCURRENTLY ', '')
                    session.execute(text(query))
                    session.commit()
                    
                    logger.info(f"✅ Index {index['name']} created successfully")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Index {index['name']} creation skipped: {e}")
                    # Continue with other indexes even if one fails
                    session.rollback()
                    continue
            
            # Check existing indexes
            logger.info("📋 Checking existing indexes...")
            result = session.execute(text("""
                SELECT schemaname, tablename, indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename IN ('saved_recipes', 'recipe_ratings')
                ORDER BY tablename, indexname;
            """))
            
            indexes_info = result.fetchall()
            logger.info(f"📊 Found {len(indexes_info)} indexes on recipes tables:")
            
            for idx in indexes_info:
                logger.info(f"  - {idx[2]} on {idx[1]}")
            
            logger.info("✅ Database optimization completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False
    
    return True

def analyze_query_performance():
    """Analyze query performance for recipes"""
    try:
        with get_db_session() as session:
            logger.info("📊 Analyzing query performance...")
            
            # Check table statistics
            result = session.execute(text("""
                SELECT 
                    schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del,
                    n_live_tup, n_dead_tup, last_vacuum, last_autovacuum,
                    last_analyze, last_autoanalyze
                FROM pg_stat_user_tables 
                WHERE tablename IN ('saved_recipes', 'recipe_ratings');
            """))
            
            stats = result.fetchall()
            for stat in stats:
                logger.info(f"📊 Table {stat[1]}: {stat[5]} live rows, last analyzed: {stat[9]}")
            
            # Sample query explain plan
            logger.info("🔍 Sample query explain plan:")
            sample_user_id = '00000000-0000-0000-0000-000000000000'  # dummy UUID
            
            result = session.execute(text("""
                EXPLAIN (ANALYZE, BUFFERS) 
                SELECT r.id, r.name, r.updated_at
                FROM saved_recipes r 
                WHERE r.user_id = :user_id 
                ORDER BY r.updated_at DESC 
                LIMIT 10;
            """), {'user_id': sample_user_id})
            
            plan = result.fetchall()
            for line in plan:
                logger.info(f"  {line[0]}")
                
    except Exception as e:
        logger.warning(f"⚠️ Performance analysis failed: {e}")

if __name__ == "__main__":
    logger.info("🚀 Database Optimization Script Starting...")
    
    success = create_performance_indexes()
    
    if success:
        analyze_query_performance()
        logger.info("🎉 Database optimization completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database optimization failed!")
        sys.exit(1)