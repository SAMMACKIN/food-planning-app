"""
Migration to update ingredient categories from old structure to new improved structure
Handles existing data by migrating ingredients from old categories to new ones
"""
import logging
from sqlalchemy import text
from app.core.database_service import get_db_session
from app.models.ingredient import IngredientCategory, Ingredient
from app.data.ingredients_data import INGREDIENT_CATEGORIES, INGREDIENTS_DATA

logger = logging.getLogger(__name__)

def migrate_ingredient_categories():
    """Update ingredient categories to new improved structure"""
    logger.info("🔄 Starting ingredient category migration...")
    
    try:
        with get_db_session() as session:
            # Check current state
            existing_categories = session.query(IngredientCategory).all()
            existing_cat_names = {cat.name for cat in existing_categories}
            existing_ingredients = session.query(Ingredient).all()
            
            logger.info(f"Found {len(existing_categories)} existing categories: {list(existing_cat_names)}")
            logger.info(f"Found {len(existing_ingredients)} existing ingredients")
            
            # Create mapping of old category names to new category names
            category_mapping = {
                "Proteins": {
                    # Meat & Poultry
                    "Chicken Breast": "Meat & Poultry",
                    "Chicken Thighs": "Meat & Poultry", 
                    "Ground Beef": "Meat & Poultry",
                    "Ground Turkey": "Meat & Poultry",
                    "Pork Chops": "Meat & Poultry",
                    "Turkey Breast": "Meat & Poultry",
                    "Ham": "Meat & Poultry",
                    "Bacon": "Meat & Poultry",
                    
                    # Fish & Seafood
                    "Salmon": "Fish & Seafood",
                    "Tuna": "Fish & Seafood",
                    "Cod": "Fish & Seafood", 
                    "Shrimp": "Fish & Seafood",
                    "Crab": "Fish & Seafood",
                    
                    # Legumes & Plant Proteins
                    "Black Beans": "Legumes & Plant Proteins",
                    "Kidney Beans": "Legumes & Plant Proteins",
                    "Chickpeas": "Legumes & Plant Proteins",
                    "Lentils": "Legumes & Plant Proteins",
                    "Tofu": "Legumes & Plant Proteins",
                    "Tempeh": "Legumes & Plant Proteins",
                    "Protein Powder": "Legumes & Plant Proteins",
                    
                    # Eggs & Dairy Proteins  
                    "Eggs": "Eggs & Dairy Proteins",
                    "Egg Whites": "Eggs & Dairy Proteins",
                    "Greek Yogurt": "Eggs & Dairy Proteins",
                    "Cottage Cheese": "Eggs & Dairy Proteins",
                },
                "Grains": "Grains & Starches",
                "Spices & Herbs": "Herbs & Spices",
                # Dairy category moves some items to new protein categories, but keeps most
                "Dairy": {
                    "Greek Yogurt": "Eggs & Dairy Proteins",
                    "Cottage Cheese": "Eggs & Dairy Proteins",
                    # All other dairy items stay in Dairy category
                }
            }
            
            # Step 1: Create new categories that don't exist
            category_objects = {cat.name: cat for cat in existing_categories}
            new_categories_created = 0
            
            for cat_name in INGREDIENT_CATEGORIES:
                if cat_name not in existing_cat_names:
                    category = IngredientCategory(name=cat_name)
                    session.add(category)
                    session.flush()  # Get the ID
                    category_objects[cat_name] = category
                    new_categories_created += 1
                    logger.info(f"  + Created category: {cat_name}")
            
            # Commit new categories
            if new_categories_created > 0:
                session.commit()
                logger.info(f"✅ Created {new_categories_created} new categories")
            
            # Step 2: Migrate existing ingredients to new categories
            migrated_count = 0
            
            for ingredient in existing_ingredients:
                old_category = ingredient.category
                if not old_category:
                    continue
                    
                new_category_name = None
                
                # Check if this ingredient needs to be moved
                if old_category.name in category_mapping:
                    mapping = category_mapping[old_category.name]
                    
                    if isinstance(mapping, str):
                        # Simple mapping (e.g., "Grains" -> "Grains & Starches")
                        new_category_name = mapping
                    elif isinstance(mapping, dict):
                        # Complex mapping based on ingredient name
                        new_category_name = mapping.get(ingredient.name)
                        
                        # For Dairy category, if not explicitly mapped, keep in Dairy
                        if old_category.name == "Dairy" and not new_category_name:
                            continue  # Stay in Dairy
                
                # Update ingredient category if mapping found
                if new_category_name and new_category_name in category_objects:
                    old_cat_name = old_category.name
                    ingredient.category_id = category_objects[new_category_name].id
                    migrated_count += 1
                    logger.info(f"  → Moved '{ingredient.name}' from '{old_cat_name}' to '{new_category_name}'")
            
            # Step 3: Add any missing ingredients from centralized data
            existing_ingredient_names = {ing.name for ing in existing_ingredients}
            added_count = 0
            
            for name, category_name, unit, nutrition in INGREDIENTS_DATA:
                if name not in existing_ingredient_names and category_name in category_objects:
                    ingredient = Ingredient(
                        name=name,
                        category_id=category_objects[category_name].id,
                        unit=unit,
                        nutritional_info=nutrition,
                        allergens=[]
                    )
                    session.add(ingredient)
                    added_count += 1
                    logger.info(f"  + Added new ingredient: {name} ({category_name})")
            
            # Step 4: Remove empty old categories
            removed_categories = 0
            for category in existing_categories:
                # Refresh ingredient count
                ingredient_count = session.query(Ingredient).filter(
                    Ingredient.category_id == category.id
                ).count()
                
                # Remove category if it's empty and was part of old structure
                if ingredient_count == 0 and category.name in ["Proteins"]:
                    session.delete(category)
                    removed_categories += 1
                    logger.info(f"  - Removed empty category: {category.name}")
            
            # Commit all changes
            session.commit()
            
            # Final summary
            total_categories = session.query(IngredientCategory).count()
            total_ingredients = session.query(Ingredient).count()
            
            logger.info(f"✅ Migration completed successfully!")
            logger.info(f"📊 Summary:")
            logger.info(f"   - Created {new_categories_created} new categories")
            logger.info(f"   - Migrated {migrated_count} existing ingredients")
            logger.info(f"   - Added {added_count} new ingredients")
            logger.info(f"   - Removed {removed_categories} empty categories")
            logger.info(f"   - Final totals: {total_categories} categories, {total_ingredients} ingredients")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error during ingredient category migration: {e}")
        return False

if __name__ == "__main__":
    migrate_ingredient_categories()