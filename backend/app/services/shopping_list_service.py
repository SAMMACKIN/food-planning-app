"""
Shopping List Service - Generate shopping lists from meal plans
"""
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.shopping import ShoppingList, ShoppingListItem
from ..models.meal_plan import MealPlan
from ..models.recipe_v2 import RecipeV2
from ..models.pantry import PantryItem
from ..schemas.shopping import GenerateShoppingListRequest

logger = logging.getLogger(__name__)


class ShoppingListService:
    """Service for generating and managing shopping lists"""
    
    # Category mappings for common ingredients
    INGREDIENT_CATEGORIES = {
        'produce': [
            'tomato', 'onion', 'garlic', 'bell pepper', 'carrot', 'celery', 'lettuce', 
            'spinach', 'broccoli', 'cauliflower', 'cucumber', 'avocado', 'lemon', 
            'lime', 'apple', 'banana', 'orange', 'potato', 'sweet potato', 'mushroom',
            'zucchini', 'eggplant', 'corn', 'peas', 'green beans', 'asparagus'
        ],
        'dairy': [
            'milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'eggs',
            'cottage cheese', 'cream cheese', 'mozzarella', 'cheddar', 'parmesan'
        ],
        'meat': [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp', 'turkey',
            'ham', 'bacon', 'sausage', 'ground beef', 'ground turkey', 'lamb'
        ],
        'pantry': [
            'rice', 'pasta', 'flour', 'sugar', 'salt', 'pepper', 'oil', 'olive oil',
            'vinegar', 'baking powder', 'baking soda', 'vanilla', 'spices', 'herbs',
            'beans', 'canned tomatoes', 'tomato sauce', 'broth', 'stock'
        ],
        'bakery': [
            'bread', 'rolls', 'bagels', 'tortillas', 'pita', 'croissants', 'muffins'
        ],
        'frozen': [
            'frozen vegetables', 'frozen fruit', 'ice cream', 'frozen pizza', 
            'frozen chicken', 'frozen fish', 'frozen berries'
        ],
        'beverages': [
            'water', 'juice', 'soda', 'coffee', 'tea', 'wine', 'beer', 'milk',
            'coconut milk', 'almond milk'
        ],
        'snacks': [
            'chips', 'crackers', 'nuts', 'granola', 'cookies', 'candy', 'popcorn'
        ]
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_from_meal_plans(
        self, 
        user_id: str, 
        request: GenerateShoppingListRequest
    ) -> ShoppingList:
        """Generate a shopping list from meal plans for a given week"""
        
        try:
            logger.info(f"🛒 Generating shopping list for user {user_id}, week starting {request.week_start}")
            
            # Determine week end if not provided
            week_end = request.week_end or (request.week_start + timedelta(days=7))
            
            # Get meal plans for the specified period
            meal_plans = self._get_meal_plans_for_period(user_id, request.week_start, week_end, request.meal_plan_ids)
            logger.info(f"📅 Found {len(meal_plans)} meal plans for the period")
            
            # Aggregate ingredients from meal plans
            ingredient_needs = self._aggregate_ingredients_from_meal_plans(meal_plans)
            logger.info(f"🥘 Aggregated {len(ingredient_needs)} unique ingredients")
            
            # Subtract pantry inventory if requested
            if request.include_pantry_check:
                ingredient_needs = self._subtract_pantry_inventory(user_id, ingredient_needs)
                logger.info(f"🏠 After pantry check: {len([k for k, v in ingredient_needs.items() if v['quantity'] > 0])} items needed")
            
            # Create shopping list name if not provided
            list_name = request.name or f"Week of {request.week_start.strftime('%B %d, %Y')}"
            
            # Create the shopping list
            shopping_list = ShoppingList(
                user_id=user_id,
                name=list_name,
                week_start=request.week_start,
                total_items=0,
                completed_items=0,
                estimated_total_cost=0.0
            )
            self.db.add(shopping_list)
            self.db.flush()  # Get the ID
            
            # Create shopping list items
            items_created = 0
            total_estimated_cost = 0.0
            
            for ingredient_name, data in ingredient_needs.items():
                if data['quantity'] > 0:  # Only add items with positive quantities
                    item = ShoppingListItem(
                        shopping_list_id=shopping_list.id,
                        ingredient_id=data.get('ingredient_id'),
                        name=ingredient_name,
                        quantity=round(data['quantity'], 2),
                        unit=data.get('unit', ''),
                        category=data.get('category', 'other'),
                        source_recipes=data.get('source_recipes', []),
                        source_meal_plans=data.get('meal_plan_ids', []),
                        estimated_cost=data.get('estimated_cost', 0.0)
                    )
                    self.db.add(item)
                    items_created += 1
                    total_estimated_cost += data.get('estimated_cost', 0.0)
            
            # Update shopping list totals
            shopping_list.total_items = items_created
            shopping_list.estimated_total_cost = round(total_estimated_cost, 2)
            
            self.db.commit()
            
            logger.info(f"✅ Shopping list created with {items_created} items, estimated cost: ${total_estimated_cost:.2f}")
            return shopping_list
            
        except Exception as e:
            logger.error(f"❌ Error generating shopping list: {e}")
            self.db.rollback()
            raise
    
    def _get_meal_plans_for_period(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        meal_plan_ids: Optional[List[str]] = None
    ) -> List[MealPlan]:
        """Get meal plans for a specific period or specific IDs"""
        
        query = self.db.query(MealPlan).filter(MealPlan.user_id == user_id)
        
        if meal_plan_ids:
            # Use specific meal plan IDs
            query = query.filter(MealPlan.id.in_(meal_plan_ids))
        else:
            # Use date range
            query = query.filter(
                MealPlan.date >= start_date,
                MealPlan.date < end_date
            )
        
        return query.all()
    
    def _aggregate_ingredients_from_meal_plans(self, meal_plans: List[MealPlan]) -> Dict[str, Dict[str, Any]]:
        """Aggregate ingredients needed from multiple meal plans"""
        
        ingredients_needed = defaultdict(lambda: {
            'quantity': 0.0,
            'unit': '',
            'category': 'other',
            'source_recipes': [],
            'meal_plan_ids': [],
            'estimated_cost': 0.0,
            'ingredient_id': None
        })
        
        for meal_plan in meal_plans:
            if not meal_plan.recipe_id:
                continue
                
            # Get the recipe
            recipe = self.db.query(RecipeV2).filter(RecipeV2.id == meal_plan.recipe_id).first()
            if not recipe or not recipe.ingredients_needed:
                continue
            
            # Calculate servings multiplier
            servings_multiplier = meal_plan.servings / recipe.servings if recipe.servings else 1
            
            # Process each ingredient in the recipe
            for ingredient_data in recipe.ingredients_needed:
                if not isinstance(ingredient_data, dict):
                    continue
                
                ingredient_name = ingredient_data.get('name', '').strip().lower()
                if not ingredient_name:
                    continue
                
                # Normalize ingredient name for grouping
                normalized_name = self._normalize_ingredient_name(ingredient_name)
                
                # Get quantity and unit
                quantity = float(ingredient_data.get('quantity', 0)) * servings_multiplier
                unit = ingredient_data.get('unit', '').strip()
                
                # Add to aggregated data
                ingredients_needed[normalized_name]['quantity'] += quantity
                if not ingredients_needed[normalized_name]['unit'] and unit:
                    ingredients_needed[normalized_name]['unit'] = unit
                
                # Add recipe to source list
                if recipe.name not in ingredients_needed[normalized_name]['source_recipes']:
                    ingredients_needed[normalized_name]['source_recipes'].append(recipe.name)
                
                # Add meal plan ID
                meal_plan_str = str(meal_plan.id)
                if meal_plan_str not in ingredients_needed[normalized_name]['meal_plan_ids']:
                    ingredients_needed[normalized_name]['meal_plan_ids'].append(meal_plan_str)
                
                # Set category and cost estimate
                if ingredients_needed[normalized_name]['category'] == 'other':
                    ingredients_needed[normalized_name]['category'] = self._get_ingredient_category(normalized_name)
                
                # Simple cost estimation (this could be enhanced with a price database)
                ingredients_needed[normalized_name]['estimated_cost'] += self._estimate_ingredient_cost(
                    normalized_name, quantity, unit
                )
        
        return dict(ingredients_needed)
    
    def _subtract_pantry_inventory(self, user_id: str, ingredient_needs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Subtract available pantry items from shopping needs"""
        
        # Get user's pantry items
        pantry_items = self.db.query(PantryItem).filter(
            PantryItem.user_id == user_id,
            PantryItem.quantity > 0
        ).all()
        
        # Create lookup by normalized ingredient name
        pantry_lookup = {}
        for item in pantry_items:
            if item.ingredient and item.ingredient.name:
                normalized_name = self._normalize_ingredient_name(item.ingredient.name)
                pantry_lookup[normalized_name] = item
        
        # Subtract pantry quantities from needs
        for ingredient_name, data in ingredient_needs.items():
            if ingredient_name in pantry_lookup:
                pantry_item = pantry_lookup[ingredient_name]
                available_quantity = pantry_item.quantity
                
                # Simple unit conversion - this could be enhanced
                if self._units_compatible(data.get('unit', ''), pantry_item.unit):
                    needed_quantity = data['quantity']
                    data['quantity'] = max(0, needed_quantity - available_quantity)
                    data['pantry_available'] = available_quantity
        
        return ingredient_needs
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient names for consistent grouping"""
        normalized = name.lower().strip()
        
        # Remove common modifiers
        modifiers = ['fresh', 'frozen', 'canned', 'dried', 'organic', 'whole', 'sliced', 'diced', 'chopped']
        for modifier in modifiers:
            normalized = normalized.replace(f'{modifier} ', '').replace(f' {modifier}', '')
        
        # Handle plurals (simple approach)
        if normalized.endswith('ies'):
            normalized = normalized[:-3] + 'y'
        elif normalized.endswith('es'):
            normalized = normalized[:-2]
        elif normalized.endswith('s') and len(normalized) > 3:
            normalized = normalized[:-1]
        
        return normalized.strip()
    
    def _get_ingredient_category(self, ingredient_name: str) -> str:
        """Categorize ingredient by name"""
        ingredient_lower = ingredient_name.lower()
        
        for category, ingredients in self.INGREDIENT_CATEGORIES.items():
            for ingredient in ingredients:
                if ingredient in ingredient_lower or ingredient_lower in ingredient:
                    return category
        
        return 'other'
    
    def _estimate_ingredient_cost(self, ingredient_name: str, quantity: float, unit: str) -> float:
        """Simple cost estimation - could be enhanced with real price data"""
        
        # Base costs per category (rough estimates)
        base_costs = {
            'produce': 2.50,
            'dairy': 3.00,
            'meat': 8.00,
            'pantry': 1.50,
            'bakery': 2.00,
            'frozen': 3.50,
            'beverages': 2.00,
            'snacks': 3.00,
            'other': 2.00
        }
        
        category = self._get_ingredient_category(ingredient_name)
        base_cost = base_costs.get(category, 2.00)
        
        # Adjust for quantity (very rough estimation)
        quantity_multiplier = max(0.5, min(3.0, quantity / 2))
        
        return round(base_cost * quantity_multiplier, 2)
    
    def _units_compatible(self, unit1: str, unit2: str) -> bool:
        """Check if two units are compatible for subtraction"""
        if not unit1 or not unit2:
            return True  # Assume compatible if either is empty
        
        # Normalize units
        unit1 = unit1.lower().strip()
        unit2 = unit2.lower().strip()
        
        # Same unit
        if unit1 == unit2:
            return True
        
        # Common equivalencies (this could be much more sophisticated)
        weight_units = {'lb', 'lbs', 'pound', 'pounds', 'oz', 'ounce', 'ounces', 'g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms'}
        volume_units = {'cup', 'cups', 'tbsp', 'tablespoon', 'tablespoons', 'tsp', 'teaspoon', 'teaspoons', 'fl oz', 'ml', 'l', 'liter', 'liters'}
        count_units = {'piece', 'pieces', 'item', 'items', 'each', 'whole'}
        
        if unit1 in weight_units and unit2 in weight_units:
            return True
        if unit1 in volume_units and unit2 in volume_units:
            return True
        if unit1 in count_units and unit2 in count_units:
            return True
        
        return False
    
    def add_manual_item(self, shopping_list_id: str, user_id: str, item_data: Dict[str, Any]) -> ShoppingListItem:
        """Add a manual item to shopping list"""
        
        # Verify shopping list ownership
        shopping_list = self.db.query(ShoppingList).filter(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == user_id
        ).first()
        
        if not shopping_list:
            raise ValueError("Shopping list not found")
        
        # Create item
        item = ShoppingListItem(
            shopping_list_id=shopping_list_id,
            name=item_data['name'],
            quantity=item_data['quantity'],
            unit=item_data.get('unit', ''),
            category=item_data.get('category', self._get_ingredient_category(item_data['name'])),
            priority=item_data.get('priority', 'normal'),
            notes=item_data.get('notes'),
            estimated_cost=item_data.get('estimated_cost', 0.0),
            manually_added=True
        )
        
        self.db.add(item)
        
        # Update shopping list totals
        shopping_list.total_items += 1
        shopping_list.estimated_total_cost += item.estimated_cost or 0.0
        
        self.db.commit()
        
        return item
    
    def toggle_item_completion(self, item_id: str, user_id: str) -> ShoppingListItem:
        """Toggle completion status of a shopping list item"""
        
        # Get item with shopping list check
        item = self.db.query(ShoppingListItem).join(ShoppingList).filter(
            ShoppingListItem.id == item_id,
            ShoppingList.user_id == user_id
        ).first()
        
        if not item:
            raise ValueError("Shopping list item not found")
        
        # Toggle completion
        was_completed = item.is_completed
        item.is_completed = not was_completed
        item.completed_at = datetime.utcnow() if item.is_completed else None
        
        # Update shopping list completed count
        shopping_list = item.shopping_list
        if item.is_completed and not was_completed:
            shopping_list.completed_items += 1
        elif not item.is_completed and was_completed:
            shopping_list.completed_items = max(0, shopping_list.completed_items - 1)
        
        self.db.commit()
        
        return item
    
    def bulk_toggle_items(self, item_ids: List[str], user_id: str, completed: bool) -> int:
        """Toggle completion status for multiple items"""
        
        # Get items with shopping list check
        items = self.db.query(ShoppingListItem).join(ShoppingList).filter(
            ShoppingListItem.id.in_(item_ids),
            ShoppingList.user_id == user_id
        ).all()
        
        if not items:
            return 0
        
        # Group by shopping list for efficient updating
        shopping_lists = {}
        updated_count = 0
        
        for item in items:
            if item.is_completed != completed:  # Only update if status is changing
                item.is_completed = completed
                item.completed_at = datetime.utcnow() if completed else None
                
                # Track shopping list changes
                list_id = item.shopping_list_id
                if list_id not in shopping_lists:
                    shopping_lists[list_id] = {'list': item.shopping_list, 'change': 0}
                
                shopping_lists[list_id]['change'] += 1 if completed else -1
                updated_count += 1
        
        # Update shopping list completed counts
        for list_data in shopping_lists.values():
            shopping_list = list_data['list']
            change = list_data['change']
            shopping_list.completed_items = max(0, shopping_list.completed_items + change)
        
        self.db.commit()
        
        return updated_count