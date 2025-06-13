import os
import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found. Claude recommendations will be disabled.")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
    
    def is_available(self) -> bool:
        """Check if Claude API is available"""
        return self.client is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_meal_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
        num_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered meal recommendations based on family preferences and pantry items
        """
        print(f"🤖 CLAUDE SERVICE CALLED at {__import__('datetime').datetime.now()}")
        print(f"🔑 Client available: {self.client is not None}")
        print(f"🔄 Requesting {num_recommendations} recommendations")
        
        if not self.client:
            print("❌ No Claude client - using fallback")
            return self._get_fallback_recommendations()

        try:
            # Build the prompt
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations
            )
            
            # Log the prompt being sent
            logger.info("=" * 80)
            logger.info("PROMPT BEING SENT TO CLAUDE:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            
            # Call Claude API (using cheapest model)
            logger.info("Calling Claude API for meal recommendations...")
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Cheapest Claude model
                max_tokens=4096,  # Maximum allowed for Haiku
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            logger.info("Claude API response received successfully")
            
            # Log the raw response
            logger.info("=" * 80)
            logger.info("RAW CLAUDE RESPONSE:")
            logger.info("=" * 80)
            logger.info(response.content[0].text)
            logger.info("=" * 80)
            
            # Parse the response
            logger.info("Parsing Claude response...")
            recommendations = self._parse_claude_response(response.content[0].text)
            logger.info(f"Parsed {len(recommendations)} recommendations from Claude response")
            
            # Log parsed recommendations
            for i, rec in enumerate(recommendations):
                logger.info(f"Recommendation {i+1}: {rec.get('name', 'NO_NAME')}")
            
            # Add AI indicator to each recommendation
            for rec in recommendations:
                rec['ai_generated'] = True
                rec['tags'] = rec.get('tags', []) + ['AI-Generated']
            
            logger.info(f"Successfully generated {len(recommendations)} meal recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting Claude recommendations: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {str(e)}")
            return self._get_fallback_recommendations()

    def _build_recommendation_prompt(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> str:
        """Build a comprehensive prompt for Claude"""
        
        # Family information with detailed preferences
        family_info = []
        for member in family_members:
            info = f"- {member['name']}"
            if member.get('age'):
                info += f" (age {member['age']})"
            
            # Add dietary restrictions
            if member.get('dietary_restrictions'):
                info += f", dietary restrictions: {', '.join(member['dietary_restrictions'])}"
            
            # Add food preferences
            preferences = member.get('preferences', {})
            if preferences.get('likes'):
                info += f", likes: {', '.join(preferences['likes'])}"
            if preferences.get('dislikes'):
                info += f", dislikes: {', '.join(preferences['dislikes'])}"
            if preferences.get('preferred_cuisines'):
                info += f", preferred cuisines: {', '.join(preferences['preferred_cuisines'])}"
                
            family_info.append(info)
        
        # Pantry inventory
        pantry_by_category = {}
        for item in pantry_items:
            category = item['ingredient']['category']
            if category not in pantry_by_category:
                pantry_by_category[category] = []
            pantry_by_category[category].append(
                f"{item['ingredient']['name']} ({item['quantity']} {item['ingredient']['unit']})"
            )
        
        pantry_info = []
        for category, items in pantry_by_category.items():
            pantry_info.append(f"{category}: {', '.join(items)}")
        
        prompt = f"""
Create {num_recommendations} personalized meal recommendations in valid JSON format:

FAMILY MEMBERS & PREFERENCES:
{chr(10).join(family_info)}

AVAILABLE PANTRY ITEMS:
{chr(10).join(pantry_info)}

INSTRUCTIONS:
- PRIORITIZE family food likes and preferred cuisines
- AVOID family food dislikes completely
- RESPECT all dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Use pantry ingredients when possible
- Include variety in cuisines based on preferences
- Consider age-appropriate meals for children

Return ONLY valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "name": "Recipe Name",
      "description": "Short description highlighting why it fits family preferences",
      "prep_time": 30,
      "difficulty": "Easy",
      "servings": 4,
      "ingredients_needed": [
        {{"name": "ingredient", "quantity": "1", "unit": "cup", "have_in_pantry": true}}
      ],
      "instructions": ["Step 1", "Step 2"],
      "tags": ["cuisine-type", "dietary-restriction", "family-friendly"],
      "nutrition_notes": "Brief notes mentioning dietary considerations",
      "pantry_usage_score": 80
    }}
  ]
}}
"""
        return prompt

    def _parse_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's JSON response"""
        try:
            logger.info(f"Starting to parse response of length: {len(response_text)}")
            
            # Extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            logger.info(f"JSON boundaries: start={start_idx}, end={end_idx}")
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON found in Claude response")
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            logger.info(f"Extracted JSON string (first 200 chars): {json_str[:200]}...")
            
            data = json.loads(json_str)
            logger.info(f"Successfully parsed JSON. Keys: {list(data.keys())}")
            
            recommendations = data.get('recommendations', [])
            logger.info(f"Found {len(recommendations)} recommendations in response")
            
            # Validate and clean up the recommendations
            cleaned_recommendations = []
            for i, rec in enumerate(recommendations):
                logger.info(f"Validating recommendation {i+1}: {rec.get('name', 'NO_NAME')}")
                if self._validate_recommendation(rec):
                    cleaned_recommendations.append(rec)
                    logger.info(f"  ✓ Valid")
                else:
                    logger.warning(f"  ✗ Invalid - missing required fields")
            
            logger.info(f"Returning {len(cleaned_recommendations)} valid recommendations")
            return cleaned_recommendations
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing Claude response: {e}")
            logger.error(f"Response text that failed to parse: {response_text[:500]}...")
            logger.warning("Falling back to default recommendations")
            return self._get_fallback_recommendations()

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate a single recommendation"""
        required_fields = ['name', 'description', 'prep_time', 'difficulty', 'servings']
        return all(field in rec for field in required_fields)

    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """NO MORE FALLBACK RECIPES - Force debugging by raising an exception"""
        logger.error("🚨 CLAUDE API FAILED - NO FALLBACK RECIPES AVAILABLE")
        print(f"🚨 CLAUDE API FAILURE at {__import__('datetime').datetime.now()}")
        import traceback
        print("🔍 FAILURE STACK TRACE:")
        traceback.print_stack()
        
        # Instead of returning fallback recipes, raise an exception to force fixing the issue
        raise Exception("Claude API failed and fallback recipes have been disabled. Check Claude API configuration and token limits.")

# Global instance
claude_service = ClaudeService()