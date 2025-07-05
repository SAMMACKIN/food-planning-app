-- Critical performance indexes for saved_recipes table
-- These indexes will dramatically improve query performance

-- Primary user_id index (most important)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_user_id 
ON saved_recipes(user_id);

-- Compound index for user_id + ordering (most efficient for main query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_user_updated 
ON saved_recipes(user_id, updated_at DESC);

-- Search performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_name 
ON saved_recipes(name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_difficulty 
ON saved_recipes(difficulty);

-- Recipe ratings performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipe_ratings_recipe_id 
ON recipe_ratings(recipe_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipe_ratings_user_id 
ON recipe_ratings(user_id);

-- Compound index for rating aggregation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recipe_ratings_recipe_rating 
ON recipe_ratings(recipe_id, rating);

-- Text search indexes for tags and descriptions (optional, for advanced search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_tags_gin 
ON saved_recipes USING gin(to_tsvector('english', COALESCE(tags, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_recipes_description_gin 
ON saved_recipes USING gin(to_tsvector('english', COALESCE(description, '')));