-- Critical performance indexes for recipes_v2 table
-- These indexes will dramatically improve query performance

-- Primary user_id index (most important)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_user_id 
ON recipes_v2(user_id);

-- Compound index for user_id + ordering (most efficient for main query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_user_updated 
ON recipes_v2(user_id, updated_at DESC);

-- Search performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_name 
ON recipes_v2(name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_difficulty 
ON recipes_v2(difficulty);

-- Text search indexes for tags and descriptions (optional, for advanced search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_tags_gin 
ON recipes_v2 USING gin(to_tsvector('english', COALESCE(tags::text, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipes_v2_description_gin 
ON recipes_v2 USING gin(to_tsvector('english', COALESCE(description, '')));