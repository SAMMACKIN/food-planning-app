import os
import json
from typing import List, Dict, Any, Optional, Literal
from anthropic import Anthropic
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AIProvider = Literal["claude", "groq"]

class AIService:
    def __init__(self):
        # Initialize Claude
        self.claude_client = None
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key:
            self.claude_client = Anthropic(api_key=claude_key)
            logger.info("Claude client initialized")
        else:
            logger.warning("ANTHROPIC_API_KEY not found. Claude will be disabled.")
        
        # Initialize Groq
        self.groq_client = None
        groq_key = os.getenv("GROQ_API_KEY", "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")
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)
            logger.info("Groq client initialized")
        else:
            logger.warning("GROQ_API_KEY not found. Groq will be disabled.")
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of available AI providers"""
        return {
            "claude": self.claude_client is not None,
            "groq": self.groq_client is not None
        }
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if specific provider is available"""
        if provider == "claude":
            return self.claude_client is not None
        elif provider == "groq":
            return self.groq_client is not None
        return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_meal_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
        num_recommendations: int = 5,
        provider: AIProvider = "claude"
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered meal recommendations from specified provider
        """
        logger.info(f"🤖 AI SERVICE CALLED - Provider: {provider}")
        logger.info(f"🔄 Requesting {num_recommendations} recommendations")
        
        if provider == "claude" and self.claude_client:
            return await self._get_claude_recommendations(
                family_members, pantry_items, preferences, num_recommendations
            )
        elif provider == "groq" and self.groq_client:
            return await self._get_groq_recommendations(
                family_members, pantry_items, preferences, num_recommendations
            )
        else:
            logger.error(f"Provider {provider} not available or not configured")
            raise Exception(f"AI provider '{provider}' is not available")

    async def _get_claude_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Claude"""
        try:
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations
            )
            
            logger.info("Calling Claude API for meal recommendations...")
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recommendations = self._parse_ai_response(response.content[0].text, "claude")
            logger.info(f"Claude generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def _get_groq_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Groq"""
        try:
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations
            )
            
            logger.info("Calling Groq API for meal recommendations...")
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Fast, capable model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7
            )
            
            recommendations = self._parse_ai_response(response.choices[0].message.content, "groq")
            logger.info(f"Groq generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _build_recommendation_prompt(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> str:
        """Build a comprehensive prompt for AI models"""
        
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
            member_prefs = member.get('preferences', {})
            if member_prefs.get('likes'):
                info += f", likes: {', '.join(member_prefs['likes'])}"
            if member_prefs.get('dislikes'):
                info += f", dislikes: {', '.join(member_prefs['dislikes'])}"
            if member_prefs.get('preferred_cuisines'):
                info += f", preferred cuisines: {', '.join(member_prefs['preferred_cuisines'])}"
                
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

    def _parse_ai_response(self, response_text: str, provider: AIProvider) -> List[Dict[str, Any]]:
        """Parse AI response and add provider info"""
        try:
            # Extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            recommendations = data.get('recommendations', [])
            
            # Add provider info and AI indicator to each recommendation
            for rec in recommendations:
                rec['ai_generated'] = True
                rec['ai_provider'] = provider
                rec['tags'] = rec.get('tags', []) + ['AI-Generated', f'{provider.title()}-Generated']
            
            return [rec for rec in recommendations if self._validate_recommendation(rec)]
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing {provider} response: {e}")
            raise Exception(f"Failed to parse {provider} response")

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate a single recommendation"""
        required_fields = ['name', 'description', 'prep_time', 'difficulty', 'servings']
        return all(field in rec for field in required_fields)

# Global instance
ai_service = AIService()