"""
AI-powered meal recommendations API endpoints
"""
import sqlite3
import datetime
import logging
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from ..core.database import get_db_connection
from ..core.security import verify_token
from ..schemas.meals import MealRecommendationRequest, MealRecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)


def get_current_user(authorization: str = None):
    """Get current user with admin fallback"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    return verify_token(token)


# Import AI service from existing service module
try:
    import sys
    import os
    # Add the backend directory to Python path to import ai_service
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    from ai_service import ai_service
    logger.info("Successfully imported AI service")
except ImportError as e:
    logger.warning(f"Could not import AI service: {e}")
    # Fallback - create a mock service for development
    class MockAIService:
        def is_provider_available(self, provider: str) -> bool:
            return False
        
        def get_available_providers(self) -> dict:
            return {"claude": False, "groq": False}
        
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
    # Get the current authenticated user
    current_user = get_current_user(authorization)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info("=== RECOMMENDATIONS REQUEST RECEIVED ===")
    logger.info(f"Request: {request}")
    logger.info(f"Time: {datetime.datetime.now()}")
    logger.info("="*50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = current_user['id']
        
        # Get family members
        cursor.execute('''
            SELECT id, name, age, dietary_restrictions, preferences 
            FROM family_members 
            WHERE user_id = ?
        ''', (user_id,))
        family_data = cursor.fetchall()
        
        family_members = []
        for member in family_data:
            # Parse dietary_restrictions and preferences from JSON/eval
            try:
                dietary_restrictions = json.loads(member[3]) if member[3] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    dietary_restrictions = eval(member[3]) if member[3] else []
                except:
                    dietary_restrictions = []
            
            try:
                preferences = json.loads(member[4]) if member[4] else {}
            except (json.JSONDecodeError, TypeError):
                try:
                    preferences = eval(member[4]) if member[4] else {}
                except:
                    preferences = {}
            
            family_members.append({
                'id': member[0],
                'name': member[1],
                'age': member[2],
                'dietary_restrictions': dietary_restrictions,
                'preferences': preferences
            })
        
        # Get pantry items
        cursor.execute('''
            SELECT p.quantity, p.expiration_date,
                   i.id, i.name, i.category, i.unit, i.calories_per_unit, i.protein_per_unit,
                   i.carbs_per_unit, i.fat_per_unit, i.allergens
            FROM pantry_items p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.user_id = ?
        ''', (user_id,))
        pantry_data = cursor.fetchall()
        
        pantry_items = []
        for item in pantry_data:
            # Parse allergens from JSON/eval
            try:
                allergens = json.loads(item[10]) if item[10] else []
            except (json.JSONDecodeError, TypeError):
                try:
                    allergens = eval(item[10]) if item[10] else []
                except:
                    allergens = []
            
            pantry_items.append({
                'quantity': item[0],
                'expiration_date': item[1],
                'ingredient': {
                    'id': item[2],
                    'name': item[3],
                    'category': item[4],
                    'unit': item[5],
                    'calories_per_unit': item[6] or 0,
                    'protein_per_unit': item[7] or 0,
                    'carbs_per_unit': item[8] or 0,
                    'fat_per_unit': item[9] or 0,
                    'allergens': allergens
                }
            })
        
        # Get recommendations from selected AI provider
        provider = request.ai_provider or "claude"
        logger.info(f"DEBUG: Getting {request.num_recommendations} recommendations from {provider}")
        logger.info(f"DEBUG: Family members: {len(family_members)}")
        logger.info(f"DEBUG: Pantry items: {len(pantry_items)}")
        
        recommendations = await ai_service.get_meal_recommendations(
            family_members=family_members,
            pantry_items=pantry_items,
            preferences=request.preferences,
            num_recommendations=request.num_recommendations,
            provider=provider
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
    
    finally:
        conn.close()


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
        "default_provider": "claude" if providers.get("claude") else ("groq" if providers.get("groq") else None),
        "message": f"Available AI providers: {', '.join(available_providers)}" if available_providers else "No AI providers configured"
    }


@router.get("/test")
async def test_ai_recommendations(provider: str = Query(default="claude")):
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