import os
import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

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
        if not self.client:
            return self._get_fallback_recommendations()

        try:
            # Build the prompt
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations
            )
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            recommendations = self._parse_claude_response(response.content[0].text)
            logger.info(f"Successfully generated {len(recommendations)} meal recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting Claude recommendations: {e}")
            return self._get_fallback_recommendations()

    def _build_recommendation_prompt(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> str:
        """Build a comprehensive prompt for Claude"""
        
        # Family information
        family_info = []
        for member in family_members:
            info = f"- {member['name']}"
            if member.get('age'):
                info += f" (age {member['age']})"
            if member.get('dietary_restrictions'):
                info += f", dietary restrictions: {', '.join(member['dietary_restrictions'])}"
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
You are a professional meal planning assistant. Create {num_recommendations} personalized meal recommendations based on the following information:

FAMILY MEMBERS:
{chr(10).join(family_info)}

PANTRY INVENTORY:
{chr(10).join(pantry_info)}

REQUIREMENTS:
- Suggest complete meals (not just ingredients)
- Consider dietary restrictions and family size
- Prioritize using available pantry ingredients
- Include prep time and difficulty level
- Provide brief cooking instructions
- Ensure nutritional balance

RESPONSE FORMAT (return valid JSON):
{{
  "recommendations": [
    {{
      "name": "Meal Name",
      "description": "Brief description of the dish",
      "prep_time": 30,
      "difficulty": "Easy|Medium|Hard",
      "servings": 4,
      "ingredients_needed": [
        {{
          "name": "ingredient name",
          "quantity": "amount",
          "unit": "measurement",
          "have_in_pantry": true/false
        }}
      ],
      "instructions": [
        "Step 1...",
        "Step 2..."
      ],
      "tags": ["category1", "category2"],
      "nutrition_notes": "Brief nutritional highlights",
      "pantry_usage_score": 85
    }}
  ]
}}

Focus on practical, family-friendly meals that make good use of available ingredients.
"""
        return prompt

    def _parse_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            recommendations = data.get('recommendations', [])
            
            # Validate and clean up the recommendations
            cleaned_recommendations = []
            for rec in recommendations:
                if self._validate_recommendation(rec):
                    cleaned_recommendations.append(rec)
            
            return cleaned_recommendations
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing Claude response: {e}")
            return self._get_fallback_recommendations()

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate a single recommendation"""
        required_fields = ['name', 'description', 'prep_time', 'difficulty', 'servings']
        return all(field in rec for field in required_fields)

    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """Provide fallback recommendations when Claude API is unavailable"""
        return [
            {
                "name": "Simple Pasta with Garlic",
                "description": "Quick and easy pasta dish with garlic and olive oil",
                "prep_time": 20,
                "difficulty": "Easy",
                "servings": 4,
                "ingredients_needed": [
                    {"name": "Pasta", "quantity": "1", "unit": "cup", "have_in_pantry": True},
                    {"name": "Garlic", "quantity": "3", "unit": "clove", "have_in_pantry": True},
                    {"name": "Olive Oil", "quantity": "2", "unit": "tablespoon", "have_in_pantry": True}
                ],
                "instructions": [
                    "Boil pasta according to package instructions",
                    "Heat olive oil and sauté minced garlic",
                    "Toss pasta with garlic oil",
                    "Season with salt and pepper"
                ],
                "tags": ["quick", "vegetarian", "italian"],
                "nutrition_notes": "Good source of carbohydrates",
                "pantry_usage_score": 90
            },
            {
                "name": "Scrambled Eggs with Toast",
                "description": "Classic breakfast that works for any meal",
                "prep_time": 10,
                "difficulty": "Easy",
                "servings": 2,
                "ingredients_needed": [
                    {"name": "Eggs", "quantity": "4", "unit": "large", "have_in_pantry": True},
                    {"name": "Bread", "quantity": "2", "unit": "slice", "have_in_pantry": True}
                ],
                "instructions": [
                    "Crack eggs into bowl and whisk",
                    "Cook in pan over medium heat",
                    "Toast bread",
                    "Serve together"
                ],
                "tags": ["breakfast", "protein", "quick"],
                "nutrition_notes": "High in protein",
                "pantry_usage_score": 95
            },
            {
                "name": "Basic Rice Bowl",
                "description": "Simple rice dish with available vegetables",
                "prep_time": 25,
                "difficulty": "Easy",
                "servings": 3,
                "ingredients_needed": [
                    {"name": "Rice", "quantity": "1", "unit": "cup", "have_in_pantry": True}
                ],
                "instructions": [
                    "Cook rice according to package instructions",
                    "Add any available vegetables",
                    "Season to taste"
                ],
                "tags": ["simple", "filling", "customizable"],
                "nutrition_notes": "Good carbohydrate base",
                "pantry_usage_score": 80
            }
        ]

# Global instance
claude_service = ClaudeService()