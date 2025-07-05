"""
AI-powered meal recommendations API endpoints
"""
import datetime
import logging
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from ..core.database_service import get_db_session, db_service
from ..core.auth_service import AuthService
from ..schemas.meals import MealRecommendationRequest, MealRecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)


def get_current_user(authorization: str = None):
    """Get current user using AuthService"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        user = AuthService.verify_user_token(token)
        if user:
            return {
                'sub': user['id'],
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'is_admin': user['is_admin']
            }
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


# Import AI service from existing service module
try:
    import sys
    import os
    # Add the backend directory to Python path to import ai_service
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    from ai_service import ai_service
    logger.info("Successfully imported AI service")
except ImportError as e:
    logger.warning(f"Could not import AI service: {e}")
    logger.warning(f"Backend dir attempted: {os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}")
    logger.warning(f"Current sys.path: {sys.path}")
    
    # Fallback - create a mock service for development
    class MockAIService:
        def is_provider_available(self, provider: str) -> bool:
            return False
        
        def get_available_providers(self) -> dict:
            return {"claude": False, "groq": False, "perplexity": False}
        
        async def get_meal_recommendations(self, **kwargs) -> List[dict]:
            # Return mock recommendation for development
            return [{
                "name": "Simple Pasta",
                "description": "A quick and easy pasta dish",
                "prep_time": 20,
                "difficulty": "Easy",
                "servings": 2,
                "ingredients_needed": ["pasta", "olive oil", "garlic"],
                "instructions": ["Boil pasta", "Heat oil", "Mix together"],
                "tags": ["quick", "vegetarian"],
                "nutrition_notes": "Good source of carbohydrates",
                "pantry_usage_score": 85,
                "ai_generated": False,
                "ai_provider": None
            }]
    
    ai_service = MockAIService()


@router.post("", response_model=List[MealRecommendationResponse])
async def get_meal_recommendations(
    request: MealRecommendationRequest, 
    authorization: str = Header(None)
):
    """Get AI-powered meal recommendations based on family and pantry data"""
    logger.info("🔥 RECOMMENDATIONS ENDPOINT CALLED")
    logger.info(f"🔥 Authorization header present: {bool(authorization)}")
    logger.info(f"🔥 Request data: {request}")
    logger.info(f"🔥 Time: {datetime.datetime.now()}")
    
    # Get the current authenticated user
    try:
        current_user = get_current_user(authorization)
        logger.info(f"🔥 Authentication result: {bool(current_user)}")
        if current_user:
            logger.info(f"🔥 User ID: {current_user.get('sub', 'NO_ID')}")
    except Exception as e:
        logger.error(f"🔥 Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
    
    if not current_user:
        logger.error("🔥 Authentication failed - no current user")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user_id = current_user['sub']
        logger.info(f"🔥 Processing request for user: {user_id}")
        
        with get_db_session() as session:
            from sqlalchemy import text
            
            # Get family members
            logger.info("🔥 Querying family members...")
            result = session.execute(text('''
                SELECT id, name, age, dietary_restrictions, preferences 
                FROM family_members 
                WHERE user_id = :user_id
            '''), {'user_id': user_id})
            family_data = result.fetchall()
        logger.info(f"🔥 Found {len(family_data)} family members")
        
        family_members = []
        for i, member in enumerate(family_data):
            logger.info(f"🔥 Processing family member {i+1}: {member}")
            # Parse dietary_restrictions and preferences from JSON/eval
            try:
                dietary_restrictions = json.loads(member[3]) if member[3] else []
                logger.info(f"🔥 Parsed dietary restrictions via JSON: {dietary_restrictions}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"🔥 JSON parse failed for dietary restrictions: {e} - returning empty list")
                dietary_restrictions = []
            
            try:
                preferences = json.loads(member[4]) if member[4] else {}
                logger.info(f"🔥 Parsed preferences via JSON: {preferences}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"🔥 JSON parse failed for preferences: {e} - returning empty dict")
                preferences = {}
            
            family_member = {
                'id': member[0],
                'name': member[1],
                'age': member[2],
                'dietary_restrictions': dietary_restrictions,
                'preferences': preferences
            }
            logger.info(f"🔥 Added family member: {family_member}")
            family_members.append(family_member)
        
            # Get pantry items
            logger.info("🔥 Querying pantry items...")
            result = session.execute(text('''
                SELECT p.quantity, p.expiration_date,
                       i.id, i.name, i.category_id, i.unit, i.nutritional_info
                FROM pantry_items p
                JOIN ingredients i ON p.ingredient_id = i.id
                WHERE p.user_id = :user_id
            '''), {'user_id': user_id})
            pantry_data = result.fetchall()
            logger.info(f"🔥 Found {len(pantry_data)} pantry items")
            
            pantry_items = []
            for item in pantry_data:
                # Parse nutritional info from JSON
                try:
                    nutritional_info = json.loads(item[6]) if item[6] else {}
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse nutritional info for item {item[3]} - using empty dict")
                    nutritional_info = {}
                
                pantry_items.append({
                    'quantity': item[0],
                    'expiration_date': item[1],
                    'ingredient': {
                        'id': str(item[2]),
                        'name': item[3],
                        'category': item[4],
                        'unit': item[5],
                        'calories_per_unit': nutritional_info.get('calories', 0),
                        'protein_per_unit': nutritional_info.get('protein', 0),
                        'carbs_per_unit': nutritional_info.get('carbs', 0),
                        'fat_per_unit': nutritional_info.get('fat', 0),
                        'allergens': nutritional_info.get('allergens', [])
                    }
                })
        
            # Get user recipe ratings to inform AI suggestions
            result = session.execute(text('''
                SELECT r.name, r.difficulty, r.tags, r.nutrition_notes, 
                       rt.rating, rt.review_text, rt.would_make_again,
                       r.ai_generated, r.ai_provider
                FROM saved_recipes r
                JOIN recipe_ratings rt ON r.id = rt.recipe_id
                WHERE r.user_id = :user_id AND rt.rating >= 4
                ORDER BY rt.created_at DESC
                LIMIT 20
            '''), {'user_id': user_id})
            liked_recipes_data = result.fetchall()
        
        liked_recipes = []
        for recipe in liked_recipes_data:
            try:
                tags = json.loads(recipe[2]) if recipe[2] else []
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse recipe tags - using empty list")
                tags = []
            
            liked_recipes.append({
                'name': recipe[0],
                'difficulty': recipe[1],
                'tags': tags,
                'nutrition_notes': recipe[3],
                'rating': recipe[4],
                'review_text': recipe[5],
                'would_make_again': bool(recipe[6]),
                'ai_generated': bool(recipe[7]),
                'ai_provider': recipe[8]
            })
        
            # Get disliked recipes (rating <= 2) to avoid similar suggestions
            result = session.execute(text('''
                SELECT r.name, r.difficulty, r.tags, r.nutrition_notes,
                       rt.rating, rt.review_text, rt.would_make_again
                FROM saved_recipes r
                JOIN recipe_ratings rt ON r.id = rt.recipe_id
                WHERE r.user_id = :user_id AND rt.rating <= 2
                ORDER BY rt.created_at DESC
                LIMIT 10
            '''), {'user_id': user_id})
            disliked_recipes_data = result.fetchall()
        
        disliked_recipes = []
        for recipe in disliked_recipes_data:
            try:
                tags = json.loads(recipe[2]) if recipe[2] else []
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse recipe tags - using empty list")
                tags = []
            
            disliked_recipes.append({
                'name': recipe[0],
                'difficulty': recipe[1],
                'tags': tags,
                'nutrition_notes': recipe[3],
                'rating': recipe[4],
                'review_text': recipe[5],
                'would_make_again': bool(recipe[6])
            })
        
            # Get recently saved/viewed recipes to avoid suggesting very similar ones
            result = session.execute(text('''
                SELECT name, tags, difficulty, created_at
                FROM saved_recipes 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT 15
            '''), {'user_id': user_id})
            recent_recipes_data = result.fetchall()
        
            recent_recipes = []
            for recipe in recent_recipes_data:
                try:
                    tags = json.loads(recipe[1]) if recipe[1] else []
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse recent recipe tags - using empty list")
                    tags = []
                
                recent_recipes.append({
                    'name': recipe[0],
                    'tags': tags,
                    'difficulty': recipe[2]
                })
        
        # Get recommendations from selected AI provider
        provider = request.ai_provider or "perplexity"
        logger.info(f"DEBUG: Getting {request.num_recommendations} recommendations from {provider}")
        logger.info(f"DEBUG: Family members: {len(family_members)}")
        logger.info(f"DEBUG: Pantry items: {len(pantry_items)}")
        logger.info(f"DEBUG: Liked recipes: {len(liked_recipes)}")
        logger.info(f"DEBUG: Disliked recipes: {len(disliked_recipes)}")
        logger.info(f"DEBUG: Recent recipes: {len(recent_recipes)}")
        
        recommendations = await ai_service.get_meal_recommendations(
            family_members=family_members,
            pantry_items=pantry_items,
            preferences=request.preferences,
            num_recommendations=request.num_recommendations,
            provider=provider,
            liked_recipes=liked_recipes,
            disliked_recipes=disliked_recipes,
            recent_recipes=recent_recipes
        )
        
        logger.info(f"DEBUG: Got {len(recommendations)} recommendations")
        if recommendations:
            logger.info(f"DEBUG: First recommendation: {recommendations[0].get('name', 'NO_NAME')}")
            logger.info(f"DEBUG: AI Generated: {recommendations[0].get('ai_generated', 'UNKNOWN')}")
            logger.info(f"DEBUG: Tags: {recommendations[0].get('tags', [])}")
        
        response_list = [
            MealRecommendationResponse(
                name=rec['name'],
                description=rec['description'],
                prep_time=rec['prep_time'],
                difficulty=rec['difficulty'],
                servings=rec['servings'],
                ingredients_needed=rec['ingredients_needed'],
                instructions=rec['instructions'],
                tags=rec['tags'],
                nutrition_notes=rec['nutrition_notes'],
                pantry_usage_score=rec['pantry_usage_score'],
                ai_generated=rec.get('ai_generated', False),
                ai_provider=rec.get('ai_provider')
            )
            for rec in recommendations
        ]
        
        logger.info(f"RESPONSE: Returning {len(response_list)} recommendations")
        if response_list:
            logger.info(f"RESPONSE: First AI flag: {response_list[0].ai_generated}")
        
        return response_list
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/status")
async def get_recommendation_status():
    """Check status of available AI providers"""
    logger.info("🔍 Frontend checking AI provider status")
    print("🔍 AI PROVIDER STATUS CHECK - Current time:", datetime.datetime.now())
    
    providers = ai_service.get_available_providers()
    available_providers = [name for name, available in providers.items() if available]
    
    return {
        "providers": providers,
        "available_providers": available_providers,
        "default_provider": "perplexity" if providers.get("perplexity") else ("claude" if providers.get("claude") else ("groq" if providers.get("groq") else None)),
        "message": f"Available AI providers: {', '.join(available_providers)}" if available_providers else "No AI providers configured"
    }


@router.get("/test")
async def test_ai_recommendations(provider: str = Query(default="perplexity")):
    """Test endpoint to verify AI provider is working"""
    try:
        if not ai_service.is_provider_available(provider):
            return {
                "status": "PROVIDER_UNAVAILABLE",
                "provider": provider,
                "message": f"AI provider '{provider}' is not available or configured"
            }
        
        # Quick test with minimal data
        recommendations = await ai_service.get_meal_recommendations(
            family_members=[],
            pantry_items=[],
            num_recommendations=1,
            provider=provider
        )
        
        if recommendations and recommendations[0].get('ai_generated', False):
            return {
                "status": "AI_WORKING",
                "provider": provider,
                "test_recipe": recommendations[0]['name'],
                "ai_generated": recommendations[0].get('ai_generated', False),
                "ai_provider": recommendations[0].get('ai_provider'),
                "message": f"{provider.title()} AI is generating recipes successfully"
            }
        else:
            return {
                "status": "NO_RESULTS", 
                "provider": provider,
                "test_recipe": recommendations[0]['name'] if recommendations else "None",
                "message": f"{provider.title()} returned no valid recommendations"
            }
    except Exception as e:
        logger.error(f"Error testing AI recommendations: {str(e)}")
        return {
            "status": "ERROR",
            "provider": provider,
            "error": str(e),
            "message": f"Error testing {provider} AI recommendations"
        }