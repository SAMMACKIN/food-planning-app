import os
import json
import httpx
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

AIProvider = Literal["claude", "groq", "perplexity"]

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
        groq_key = os.getenv("GROQ_API_KEY")
        # Check if key exists and is not empty
        groq_key = groq_key if groq_key and groq_key.strip() else None
        logger.info(f"Groq API key present: {'Yes' if groq_key else 'No'}")
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)
            logger.info("Groq client initialized successfully")
        else:
            logger.warning("GROQ_API_KEY not found or empty. Groq will be disabled.")
        
        # Initialize Perplexity
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        # Check if key exists and is not empty
        self.perplexity_key = self.perplexity_key if self.perplexity_key and self.perplexity_key.strip() else None
        logger.info(f"Perplexity API key present: {'Yes' if self.perplexity_key else 'No'}")
        if self.perplexity_key:
            logger.info("Perplexity client initialized successfully")
        else:
            logger.warning("PERPLEXITY_API_KEY not found or empty. Perplexity will be disabled.")
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of available AI providers"""
        return {
            "claude": self.claude_client is not None,
            "groq": self.groq_client is not None,
            "perplexity": self.perplexity_key is not None
        }
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if specific provider is available"""
        if provider == "claude":
            return self.claude_client is not None
        elif provider == "groq":
            return self.groq_client is not None
        elif provider == "perplexity":
            return self.perplexity_key is not None
        return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_meal_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
        num_recommendations: int = 5,
        provider: AIProvider = "perplexity"
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered meal recommendations from specified provider
        """
        logger.info(f"🤖 AI SERVICE CALLED - Provider: {provider}")
        logger.info(f"🔄 Requesting {num_recommendations} recommendations")
        
        if provider == "groq" and self.groq_client:
            return await self._get_groq_recommendations(
                family_members, pantry_items, preferences, num_recommendations
            )
        elif provider == "claude" and self.claude_client:
            return await self._get_claude_recommendations(
                family_members, pantry_items, preferences, num_recommendations
            )
        elif provider == "perplexity" and self.perplexity_key:
            return await self._get_perplexity_recommendations(
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
                model="llama-3.1-8b-instant",  # Verified working model
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

    async def _get_perplexity_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Perplexity"""
        try:
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations
            )
            
            logger.info("Calling Perplexity API for meal recommendations...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4096,
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
            
            recommendations = self._parse_ai_response(data["choices"][0]["message"]["content"], "perplexity")
            logger.info(f"Perplexity generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
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
        
        # Extract difficulty preference if provided
        difficulty_pref = preferences.get('difficulty', 'mixed') if preferences else 'mixed'
        
        prompt = f"""
You are a world-class chef trained by Yotam Ottolenghi, Jamie Oliver, and many other renowned culinary masters. Your expertise spans global cuisines with a focus on fresh, flavorful, and accessible cooking.

Create {num_recommendations} exceptional meal recommendations in valid JSON format:

FAMILY MEMBERS & PREFERENCES:
{chr(10).join(family_info)}

AVAILABLE PANTRY ITEMS:
{chr(10).join(pantry_info)}

CHEF'S INSTRUCTIONS:
- Draw from your training with Ottolenghi (Middle Eastern, Mediterranean), Jamie Oliver (Italian, simple fresh ingredients), and other master chefs
- PRIORITIZE family food likes and preferred cuisines
- AVOID family food dislikes completely
- RESPECT all dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Use pantry ingredients creatively when possible
- Include variety in cuisines based on preferences
- Consider age-appropriate meals for children
- Difficulty preference: {difficulty_pref} (provide mix of simple and more challenging recipes if "mixed")

RECIPE QUALITY STANDARDS:
- Provide detailed, clear cooking instructions
- Include chef tips and techniques where helpful
- Suggest flavor combinations that elevate simple ingredients
- Mention texture, appearance, and presentation notes
- Include nutritional benefits and dietary considerations

Return ONLY valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "name": "Recipe Name",
      "description": "Detailed description highlighting flavors, techniques, and why it fits family preferences",
      "prep_time": 30,
      "difficulty": "Easy|Medium|Hard",
      "servings": 4,
      "ingredients_needed": [
        {{"name": "ingredient", "quantity": "1", "unit": "cup", "have_in_pantry": true}}
      ],
      "instructions": ["Step 1 with chef technique", "Step 2 with flavor notes", "Step 3 with presentation tip"],
      "tags": ["cuisine-type", "dietary-restriction", "cooking-technique", "flavor-profile"],
      "nutrition_notes": "Detailed nutritional benefits and dietary considerations",
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