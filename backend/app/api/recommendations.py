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


# Import AI service
try:
    import sys
    import os
    
    # Try multiple import paths for ai_service
    try:
        # First try: relative import from backend root
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ai_service_path = os.path.join(backend_dir, 'ai_service.py')
        
        if os.path.exists(ai_service_path):
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from ai_service import ai_service
            logger.info("Successfully imported AI service from backend root")
        else:
            raise ImportError("ai_service.py not found in backend root")
            
    except ImportError:
        # Second try: app.services.ai_service (if moved to services)
        try:
            from app.services.ai_service import ai_service
            logger.info("Successfully imported AI service from app.services")
        except ImportError:
            # Third try: create a simple mock for testing
            logger.warning("AI service not found, creating minimal mock for testing")
            
            class MinimalAIService:
                def get_available_providers(self):
                    return {"claude": False, "groq": False, "perplexity": False}
                
                def is_provider_available(self, provider: str):
                    return False
                
                async def get_meal_recommendations(self, **kwargs):
                    return [{
                        "name": "Test Recipe",
                        "description": "Test recipe for when AI service is unavailable",
                        "prep_time": 30,
                        "difficulty": "Easy",
                        "servings": 4,
                        "ingredients_needed": ["test ingredient"],
                        "instructions": ["test instruction"],
                        "tags": ["test"],
                        "nutrition_notes": "Test nutrition",
                        "pantry_usage_score": 50,
                        "ai_generated": False,
                        "ai_provider": "test"
                    }]
            
            ai_service = MinimalAIService()
            
except Exception as e:
    logger.error(f"Critical error importing AI service: {e}")
    raise


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
        
        # Initialize variables that will be populated from database
        family_members = []
        pantry_items = []
        
        with get_db_session() as session:
            from sqlalchemy import text
            
            # Get family members with simplified query - limit processing for speed
            logger.info("🔥 Querying family members...")
            try:
                result = session.execute(text('''
                    SELECT id, name, age, preferences 
                    FROM family_members 
                    WHERE user_id = :user_id
                    LIMIT 20
                '''), {'user_id': user_id})
                family_data = result.fetchall()
                logger.info("🔥 Using simplified family schema")
            except Exception as e:
                logger.error(f"🔥 Family query failed: {e}")
                family_data = []
        logger.info(f"🔥 Found {len(family_data)} family members")
        for i, member in enumerate(family_data):
            logger.info(f"🔥 Processing family member {i+1}: {member}")
            # Parse preferences from JSON and extract dietary restrictions if available
            try:
                preferences = member[3] if isinstance(member[3], dict) else (json.loads(member[3]) if member[3] else {})
                logger.info(f"🔥 Parsed preferences: {preferences}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"🔥 JSON parse failed for preferences: {e} - returning empty dict")
                preferences = {}
            
            # Extract dietary restrictions from preferences if available
            dietary_restrictions = preferences.get('dietary_restrictions', [])
            if not isinstance(dietary_restrictions, list):
                dietary_restrictions = []
            
            family_member = {
                'id': str(member[0]),
                'name': member[1],
                'age': member[2],
                'dietary_restrictions': dietary_restrictions,
                'preferences': preferences
            }
            logger.info(f"🔥 Added family member: {family_member}")
            family_members.append(family_member)
        
            # Get pantry items - limit and optimize query for speed
            logger.info("🔥 Querying pantry items...")
            result = session.execute(text('''
                SELECT p.quantity, p.expiration_date,
                       i.id, i.name, i.category_id, i.unit, i.nutritional_info
                FROM user_pantry p
                JOIN ingredients i ON p.ingredient_id = i.id
                WHERE p.user_id = :user_id AND p.quantity > 0
                ORDER BY p.updated_at DESC
                LIMIT 100
            '''), {'user_id': user_id})
            pantry_data = result.fetchall()
            logger.info(f"🔥 Found {len(pantry_data)} pantry items")
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
        
        # Get recommendations from all AI providers in parallel (default) or specified provider
        provider = request.ai_provider or "all"
        logger.info(f"DEBUG: Getting {request.num_recommendations} recommendations from {provider}")
        logger.info(f"DEBUG: Family members: {len(family_members)}")
        logger.info(f"DEBUG: Pantry items: {len(pantry_items)}")
        
        try:
            recommendations = await ai_service.get_meal_recommendations(
                family_members=family_members,
                pantry_items=pantry_items,
                preferences=request.preferences,
                num_recommendations=request.num_recommendations,
                provider=provider
            )
            logger.info(f"DEBUG: Successfully got {len(recommendations)} recommendations")
        except Exception as e:
            logger.error(f"DEBUG: AI recommendations failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get AI recommendations: {str(e)}")
        
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
        "default_provider": "all",  # Now defaults to using all providers in parallel
        "parallel_mode": True,
        "message": f"Available AI providers: {', '.join(available_providers)} (using parallel mode by default)" if available_providers else "No AI providers configured"
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