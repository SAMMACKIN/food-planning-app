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

AIProvider = Literal["claude", "groq", "perplexity", "all"]

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
            logger.info(f"Perplexity API key length: {len(self.perplexity_key)}")
            logger.info(f"Perplexity API key starts with: {self.perplexity_key[:10]}...")
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

    async def get_meal_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
        num_recommendations: int = 5,
        provider: AIProvider = "all",  # Changed default to "all"
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered meal recommendations from specified provider or all providers in parallel
        """
        logger.info(f"🤖 AI SERVICE CALLED - Provider: {provider}")
        logger.info(f"🔄 Requesting {num_recommendations} recommendations")
        
        if provider == "all":
            return await self._get_recommendations_from_all_providers(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
            )
        else:
            # Single provider mode (legacy)
            try:
                if provider == "groq" and self.groq_client:
                    return await self._get_groq_recommendations(
                        family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
                    )
                elif provider == "claude" and self.claude_client:
                    return await self._get_claude_recommendations(
                        family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
                    )
                elif provider == "perplexity" and self.perplexity_key:
                    return await self._get_perplexity_recommendations(
                        family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
                    )
                else:
                    logger.error(f"Provider {provider} not available or not configured")
                    raise Exception(f"AI provider '{provider}' is not available")
            except Exception as e:
                logger.error(f"Failed to get recommendations from {provider}: {str(e)}")
                raise
    
    async def _get_recommendations_from_all_providers(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int,
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations from all available providers in parallel"""
        import asyncio
        
        logger.info("🚀 Getting recommendations from ALL providers in parallel")
        
        # Prepare tasks for all available providers
        tasks = []
        providers = []
        
        if self.perplexity_key:
            tasks.append(self._get_perplexity_recommendations(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
            ))
            providers.append("perplexity")
            
        if self.claude_client:
            tasks.append(self._get_claude_recommendations(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
            ))
            providers.append("claude")
            
        if self.groq_client:
            tasks.append(self._get_groq_recommendations(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
            ))
            providers.append("groq")
        
        if not tasks:
            raise Exception("No AI providers are available")
        
        logger.info(f"🔄 Starting parallel requests to {len(tasks)} providers: {providers}")
        
        # Run all requests in parallel with timeout
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in parallel provider requests: {e}")
            results = [e] * len(tasks)
        
        # Collect successful results
        all_recommendations = []
        successful_providers = []
        
        for i, result in enumerate(results):
            provider_name = providers[i]
            if isinstance(result, Exception):
                logger.warning(f"Provider {provider_name} failed: {str(result)}")
            else:
                logger.info(f"✅ Provider {provider_name} returned {len(result)} recommendations")
                all_recommendations.extend(result)
                successful_providers.append(provider_name)
        
        if not all_recommendations:
            raise Exception(f"All providers failed. Attempted: {providers}")
        
        logger.info(f"🎉 Combined results: {len(all_recommendations)} recommendations from {successful_providers}")
        
        # Return up to the requested number, ensuring variety from different providers
        return self._balance_recommendations_by_provider(all_recommendations, num_recommendations)

    def _balance_recommendations_by_provider(self, recommendations: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """Balance recommendations to get variety from different providers"""
        if len(recommendations) <= target_count:
            return recommendations
        
        # Group by provider
        by_provider = {}
        for rec in recommendations:
            provider = rec.get('ai_provider', 'unknown')
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(rec)
        
        # Round-robin selection to ensure variety
        balanced = []
        provider_list = list(by_provider.keys())
        indices = {provider: 0 for provider in provider_list}
        
        while len(balanced) < target_count and any(indices[p] < len(by_provider[p]) for p in provider_list):
            for provider in provider_list:
                if len(balanced) >= target_count:
                    break
                if indices[provider] < len(by_provider[provider]):
                    balanced.append(by_provider[provider][indices[provider]])
                    indices[provider] += 1
        
        logger.info(f"🎯 Balanced selection: {len(balanced)} recipes from {len(by_provider)} providers")
        return balanced

    async def _get_claude_recommendations(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int,
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Claude"""
        try:
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
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
        num_recommendations: int,
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Groq"""
        try:
            prompt = self._build_recommendation_prompt(
                family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
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
        num_recommendations: int,
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations from Perplexity with retry logic"""
        max_attempts = 4  # Try different models
        
        for attempt in range(max_attempts):
            try:
                prompt = self._build_recommendation_prompt(
                    family_members, pantry_items, preferences, num_recommendations, liked_recipes, disliked_recipes, recent_recipes
                )
                
                logger.info(f"Calling Perplexity API for meal recommendations (attempt {attempt + 1}/{max_attempts})...")
                logger.info(f"Using API key: {self.perplexity_key[:10]}... (length: {len(self.perplexity_key)})")
                logger.info(f"Prompt length: {len(prompt)} characters")
                
                # Try different model names in order of preference
                model_candidates = [
                    "llama-3.1-sonar-small-128k",
                    "llama-3.1-sonar-large-128k", 
                    "sonar-small-chat",
                    "sonar-medium-chat"
                ]
                
                model_to_use = model_candidates[attempt % len(model_candidates)]
                logger.info(f"Trying model: {model_to_use}")
                
                request_data = {
                    "model": model_to_use,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
                logger.info(f"Request data: {json.dumps({k: v if k != 'messages' else f'[{len(v)} messages]' for k, v in request_data.items()})}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.perplexity_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_data,
                        timeout=30.0  # Reduced timeout
                    )
                    logger.info(f"Perplexity API response status: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"Perplexity API response received: {len(str(data))} characters")
                
                recommendations = self._parse_ai_response(data["choices"][0]["message"]["content"], "perplexity")
                logger.info(f"Perplexity generated {len(recommendations)} recommendations")
                return recommendations
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Perplexity API HTTP error (attempt {attempt + 1}): {e.response.status_code}")
                logger.error(f"Perplexity API response body: {e.response.text}")
                
                if attempt == max_attempts - 1:  # Last attempt
                    raise Exception(f"Perplexity API failed after {max_attempts} attempts. Last error: {e.response.status_code} - {e.response.text}")
                else:
                    logger.warning(f"Retrying Perplexity API call...")
                    
            except httpx.TimeoutException as e:
                logger.error(f"Perplexity API timeout (attempt {attempt + 1}): {e}")
                
                if attempt == max_attempts - 1:  # Last attempt
                    raise Exception(f"Perplexity API timeout after {max_attempts} attempts")
                else:
                    logger.warning(f"Retrying Perplexity API call due to timeout...")
                    
            except Exception as e:
                logger.error(f"Perplexity API error (attempt {attempt + 1}): {e}")
                logger.error(f"Error type: {type(e).__name__}")
                
                if attempt == max_attempts - 1:  # Last attempt
                    raise
                else:
                    logger.warning(f"Retrying Perplexity API call due to error...")
        
        # Should never reach here, but just in case
        raise Exception("Unexpected error in Perplexity API retry logic")

    def _build_recommendation_prompt(
        self,
        family_members: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        num_recommendations: int,
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
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
        
        # Build user preferences from ratings data
        liked_recipes_info = []
        if liked_recipes:
            for recipe in liked_recipes[:10]:  # Limit to top 10 liked recipes
                info = f"- {recipe['name']} (rated {recipe['rating']}/5)"
                if recipe.get('tags'):
                    info += f" - tags: {', '.join(recipe['tags'])}"
                if recipe.get('difficulty'):
                    info += f" - difficulty: {recipe['difficulty']}"
                if recipe.get('review_text'):
                    info += f" - review: {recipe['review_text'][:100]}..."
                liked_recipes_info.append(info)
        
        disliked_recipes_info = []
        if disliked_recipes:
            for recipe in disliked_recipes[:5]:  # Limit to top 5 disliked recipes
                info = f"- {recipe['name']} (rated {recipe['rating']}/5)"
                if recipe.get('tags'):
                    info += f" - tags: {', '.join(recipe['tags'])}"
                if recipe.get('review_text'):
                    info += f" - negative feedback: {recipe['review_text'][:100]}..."
                disliked_recipes_info.append(info)
        
        # Build recent recipes info to avoid repetition
        recent_recipes_info = []
        if recent_recipes:
            for recipe in recent_recipes[:10]:  # Limit to last 10 recipes
                info = f"- {recipe['name']}"
                if recipe.get('tags'):
                    info += f" (tags: {', '.join(recipe['tags'][:3])})"  # Show only first 3 tags
                if recipe.get('difficulty'):
                    info += f" - {recipe['difficulty']}"
                recent_recipes_info.append(info)
        
        prompt = f"""
You are a world-class chef trained by Yotam Ottolenghi, Jamie Oliver, and many other renowned culinary masters. Your expertise spans global cuisines with a focus on fresh, flavorful, and accessible cooking.

Create {num_recommendations} exceptional meal recommendations in valid JSON format:

FAMILY MEMBERS & PREFERENCES:
{chr(10).join(family_info)}

AVAILABLE PANTRY ITEMS:
{chr(10).join(pantry_info)}

USER'S RECIPE HISTORY & PREFERENCES:
{f"HIGHLY RATED RECIPES (learn from these - user loves these!):{chr(10)}{chr(10).join(liked_recipes_info)}" if liked_recipes_info else "No highly rated recipes yet."}

{f"POORLY RATED RECIPES (avoid similar recipes!):{chr(10)}{chr(10).join(disliked_recipes_info)}" if disliked_recipes_info else "No poorly rated recipes."}

{f"RECENT RECIPES (avoid suggesting very similar recipes):{chr(10)}{chr(10).join(recent_recipes_info)}" if recent_recipes_info else "No recent recipe history."}

CHEF'S INSTRUCTIONS:
- Draw from your training with Ottolenghi (Middle Eastern, Mediterranean), Jamie Oliver (Italian, simple fresh ingredients), and other master chefs
- LEARN FROM HIGHLY RATED RECIPES: suggest similar styles, techniques, ingredients, and flavors that the user has loved
- AVOID POORLY RATED RECIPES: do not suggest recipes similar to those the user disliked
- AVOID RECENT RECIPES: provide variety by not suggesting recipes too similar to recently saved ones
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