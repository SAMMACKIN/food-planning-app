#!/usr/bin/env python3
"""
Update ingredient categories and add new ingredients to existing database
Uses centralized ingredient data with improved categorization
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.database_service import get_db_session
from app.models.ingredient import IngredientCategory, Ingredient
from app.data.ingredients_data import INGREDIENT_CATEGORIES, INGREDIENTS_DATA

def update_ingredient_categories():
    """Update ingredient categories to new improved structure"""
    print("🔄 Updating ingredient categories...")
    
    try:
        with get_db_session() as session:
            # Get existing categories
            existing_categories = session.query(IngredientCategory).all()
            existing_cat_names = {cat.name for cat in existing_categories}
            
            print(f"Found {len(existing_cat_names)} existing categories: {list(existing_cat_names)}")
            
            # Add new categories that don't exist
            category_objects = {cat.name: cat for cat in existing_categories}
            added_categories = 0
            
            for cat_name in INGREDIENT_CATEGORIES:
                if cat_name not in existing_cat_names:
                    category = IngredientCategory(name=cat_name)
                    session.add(category)
                    session.flush()  # Get the ID
                    category_objects[cat_name] = category
                    added_categories += 1
                    print(f"  + Added category: {cat_name}")
            
            if added_categories > 0:
                session.commit()
                print(f"✅ Added {added_categories} new categories")
            else:
                print("ℹ️  All categories already exist")
                
            return category_objects
            
    except Exception as e:
        print(f"❌ Error updating categories: {e}")
        raise

def add_updated_ingredients():
    """Add updated ingredients from centralized data"""
    print("🌱 Adding/updating ingredients from centralized data...")
    
    try:
        with get_db_session() as session:
            # Update categories first
            category_objects = update_ingredient_categories()
            
            # Get existing ingredients to avoid duplicates
            existing_ingredients = session.query(Ingredient.name).all()
            existing_names = {ingredient.name for ingredient in existing_ingredients}
            
            print(f"Found {len(existing_names)} existing ingredients")
            
            # Add only new ingredients that don't already exist
            added_count = 0
            skipped_count = 0
            
            for name, category_name, unit, nutrition in INGREDIENTS_DATA:
                if name not in existing_names:
                    if category_name in category_objects:
                        ingredient = Ingredient(
                            name=name,
                            category_id=category_objects[category_name].id,
                            unit=unit,
                            nutritional_info=nutrition,
                            allergens=[]
                        )
                        session.add(ingredient)
                        added_count += 1
                        print(f"  + Added: {name} ({category_name})")
                    else:
                        print(f"  - Skipped (category not found): {name} ({category_name})")
                        skipped_count += 1
                else:
                    print(f"  - Skipped existing: {name}")
                    skipped_count += 1
            
            # Commit all changes
            session.commit()
            print(f"✅ Successfully added {added_count} new ingredients")
            print(f"ℹ️  Skipped {skipped_count} existing/invalid ingredients")
            
            # Show final count
            total_ingredients = session.query(Ingredient).count()
            total_categories = session.query(IngredientCategory).count()
            print(f"📊 Total: {total_categories} categories, {total_ingredients} ingredients")
            
    except Exception as e:
        print(f"❌ Error adding ingredients: {e}")
        raise

if __name__ == "__main__":
    add_updated_ingredients()