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
        # Check if we're in testing mode
        self.is_testing = os.getenv("TESTING") == "true" or os.getenv("CI") == "true"
        
        # Initialize Claude
        self.claude_client = None
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key and not (self.is_testing and claude_key.startswith("test-")):
            self.claude_client = Anthropic(api_key=claude_key)
            logger.info("Claude client initialized")
        elif self.is_testing:
            logger.info("Claude API disabled in testing mode")
        else:
            logger.warning("ANTHROPIC_API_KEY not found. Claude will be disabled.")
        
        # Initialize Groq
        self.groq_client = None
        groq_key = os.getenv("GROQ_API_KEY")
        # Check if key exists and is not empty
        groq_key = groq_key if groq_key and groq_key.strip() else None
        logger.info(f"Groq API key present: {'Yes' if groq_key else 'No'}")
        if groq_key and not (self.is_testing and groq_key.startswith("test-")):
            self.groq_client = Groq(api_key=groq_key)
            logger.info("Groq client initialized successfully")
        elif self.is_testing:
            logger.info("Groq API disabled in testing mode")
        else:
            logger.warning("GROQ_API_KEY not found or empty. Groq will be disabled.")
        
        # Initialize Perplexity
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        # Check if key exists and is not empty
        self.perplexity_key = self.perplexity_key if self.perplexity_key and self.perplexity_key.strip() else None
        logger.info(f"Perplexity API key present: {'Yes' if self.perplexity_key else 'No'}")
        if self.perplexity_key and not (self.is_testing and self.perplexity_key.startswith("test-")):
            logger.info(f"Perplexity API key length: {len(self.perplexity_key)}")
            logger.info(f"Perplexity API key starts with: {self.perplexity_key[:10]}...")
            logger.info("Perplexity client initialized successfully")
        elif self.is_testing:
            logger.info("Perplexity API disabled in testing mode")
            self.perplexity_key = None  # Disable in testing
        else:
            logger.warning("PERPLEXITY_API_KEY not found or empty. Perplexity will be disabled.")
            self.perplexity_key = None
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of available AI providers"""
        if self.is_testing:
            # In testing mode, all providers are "available" via mocking
            return {
                "claude": True,
                "groq": True,
                "perplexity": True
            }
        return {
            "claude": self.claude_client is not None,
            "groq": self.groq_client is not None,
            "perplexity": self.perplexity_key is not None
        }
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if specific provider is available"""
        if self.is_testing:
            # In testing mode, all providers are available via mocking
            return provider in ["claude", "groq", "perplexity"]
        
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
        provider: AIProvider = "all",  # Use all providers for maximum variety
        liked_recipes: Optional[List[Dict[str, Any]]] = None,
        disliked_recipes: Optional[List[Dict[str, Any]]] = None,
        recent_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered meal recommendations from specified provider or all providers in parallel
        """
        logger.info(f"🤖 AI SERVICE CALLED - Provider: {provider}")
        logger.info(f"🔄 Requesting {num_recommendations} recommendations")
        
        # In testing mode, return mock data
        if self.is_testing:
            return self._get_mock_recommendations(num_recommendations, provider)
        
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
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                logger.error(f"Claude API response: {e.response}")
            if hasattr(e, 'status_code'):
                logger.error(f"Claude API status code: {e.status_code}")
            raise Exception(f"Claude API failed: {str(e)}")

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
                
                # Try different model names in order of preference (simplified for 2025)
                model_candidates = [
                    "sonar",  # Try basic sonar first
                    "llama-3.1-sonar-small-128k-online",
                    "llama-3.1-sonar-large-128k-online", 
                    "llama-3.1-sonar-huge-128k-online"
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
                logger.error(f"Failed model: {model_to_use}")
                logger.error(f"Request URL: {e.request.url}")
                logger.error(f"Request headers: {dict(e.request.headers)}")
                
                if attempt == max_attempts - 1:  # Last attempt
                    raise Exception(f"Perplexity API failed after {max_attempts} attempts. Last error: {e.response.status_code} - {e.response.text}")
                else:
                    logger.warning(f"Retrying Perplexity API call with next model...")
                    
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

    def _get_mock_recommendations(self, num_recommendations: int, provider: AIProvider) -> List[Dict[str, Any]]:
        """Return mock recommendations for testing"""
        logger.info(f"Returning mock recommendations for testing (provider: {provider})")
        
        mock_recipes = [
            {
                "name": "Test Chicken Stir Fry",
                "description": "A quick and healthy test recipe",
                "prep_time": 25,
                "difficulty": "Easy",
                "servings": 4,
                "ingredients_needed": [
                    {"name": "chicken breast", "quantity": "2", "unit": "pieces", "have_in_pantry": True},
                    {"name": "broccoli", "quantity": "1", "unit": "cup", "have_in_pantry": True}
                ],
                "instructions": ["Cut chicken into strips", "Stir fry with vegetables", "Serve hot"],
                "tags": ["test", "healthy", "quick"],
                "nutrition_notes": "High protein, low carb test recipe",
                "pantry_usage_score": 85,
                "ai_generated": True,
                "ai_provider": provider if provider != "all" else "claude"
            },
            {
                "name": "Mock Pasta Salad",
                "description": "Test pasta recipe for CI",
                "prep_time": 15,
                "difficulty": "Easy",
                "servings": 6,
                "ingredients_needed": [
                    {"name": "pasta", "quantity": "2", "unit": "cups", "have_in_pantry": False}
                ],
                "instructions": ["Boil pasta", "Mix with dressing", "Chill before serving"],
                "tags": ["test", "vegetarian", "cold"],
                "nutrition_notes": "Carbohydrate-rich test dish",
                "pantry_usage_score": 40,
                "ai_generated": True,
                "ai_provider": provider if provider != "all" else "perplexity"
            },
            {
                "name": "Simple Test Salad",
                "description": "Basic salad for testing purposes",
                "prep_time": 10,
                "difficulty": "Easy",
                "servings": 2,
                "ingredients_needed": [
                    {"name": "lettuce", "quantity": "2", "unit": "cups", "have_in_pantry": False}
                ],
                "instructions": ["Wash lettuce", "Add dressing", "Toss and serve"],
                "tags": ["test", "healthy", "raw"],
                "nutrition_notes": "Light and refreshing test meal",
                "pantry_usage_score": 20,
                "ai_generated": True,
                "ai_provider": provider if provider != "all" else "groq"
            }
        ]
        
        return mock_recipes[:num_recommendations]

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate a single recommendation"""
        required_fields = ['name', 'description', 'prep_time', 'difficulty', 'servings']
        return all(field in rec for field in required_fields)

    async def extract_recipe_from_content(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract recipe data from web content using AI
        """
        logger.info(f"🤖 AI extracting recipe from content ({len(content)} chars)")
        
        # In testing mode, return mock data
        if self.is_testing:
            return self._get_mock_recipe_extraction(source_url)
        
        # Try providers in order of preference
        providers = ["perplexity", "claude", "groq"]
        
        for provider in providers:
            if not self.is_provider_available(provider):
                continue
                
            try:
                logger.info(f"🔄 Trying recipe extraction with {provider}")
                
                if provider == "perplexity" and self.perplexity_key:
                    result = await self._extract_recipe_perplexity(content, source_url)
                elif provider == "claude" and self.claude_client:
                    result = await self._extract_recipe_claude(content, source_url)
                elif provider == "groq" and self.groq_client:
                    result = await self._extract_recipe_groq(content, source_url)
                else:
                    continue
                
                if result and self._validate_extracted_recipe(result):
                    logger.info(f"✅ Successfully extracted recipe with {provider}: {result.get('name', 'Unknown')}")
                    return result
                    
            except Exception as e:
                logger.warning(f"❌ Recipe extraction failed with {provider}: {e}")
                continue
        
        logger.error("❌ All providers failed for recipe extraction")
        return None

    async def _extract_recipe_perplexity(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract recipe using Perplexity"""
        prompt = self._build_recipe_extraction_prompt(content, source_url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return self._parse_recipe_extraction(data["choices"][0]["message"]["content"], "perplexity")
                
        except Exception as e:
            logger.error(f"Perplexity recipe extraction error: {e}")
            raise

    async def _extract_recipe_claude(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract recipe using Claude"""
        prompt = self._build_recipe_extraction_prompt(content, source_url)
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_recipe_extraction(response.content[0].text, "claude")
            
        except Exception as e:
            logger.error(f"Claude recipe extraction error: {e}")
            raise

    async def _extract_recipe_groq(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract recipe using Groq"""
        prompt = self._build_recipe_extraction_prompt(content, source_url)
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.3
            )
            
            return self._parse_recipe_extraction(response.choices[0].message.content, "groq")
            
        except Exception as e:
            logger.error(f"Groq recipe extraction error: {e}")
            raise

    def _build_recipe_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build prompt for recipe extraction"""
        return f"""
You are a professional recipe extraction specialist. Extract recipe information from the following web content and return it in valid JSON format.

SOURCE URL: {source_url}

WEB CONTENT:
{content}

INSTRUCTIONS:
- Extract the main recipe from this content
- Parse ingredients with quantities and units when possible
- Break down instructions into clear steps
- Determine appropriate difficulty level (Easy/Medium/Hard)
- Estimate prep time if not explicitly stated
- Extract servings/yield information
- Identify relevant tags (cuisine type, dietary restrictions, etc.)
- If multiple recipes exist, extract the main/featured one

Return ONLY valid JSON in this exact format:
{{
  "name": "Recipe Name",
  "description": "Brief description of the dish",
  "prep_time": 30,
  "difficulty": "Easy|Medium|Hard",
  "servings": 4,
  "ingredients_needed": [
    {{"name": "ingredient name", "quantity": "1", "unit": "cup", "have_in_pantry": false}},
    {{"name": "ingredient name", "quantity": "2", "unit": "tsp", "have_in_pantry": false}}
  ],
  "instructions": [
    "Step 1: Detailed instruction",
    "Step 2: Next step with specifics",
    "Step 3: Continue until complete"
  ],
  "tags": ["cuisine-type", "dietary-info", "cooking-method"],
  "nutrition_notes": "Nutritional highlights or dietary information",
  "pantry_usage_score": 0
}}

IMPORTANT: Return ONLY the JSON object, no additional text or explanation.
"""

    def _parse_recipe_extraction(self, response_text: str, provider: str) -> Optional[Dict[str, Any]]:
        """Parse recipe extraction response"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            recipe_data = json.loads(json_str)
            
            # Add AI metadata
            recipe_data['ai_generated'] = True
            recipe_data['ai_provider'] = provider
            
            return recipe_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing {provider} recipe extraction: {e}")
            return None

    def _validate_extracted_recipe(self, recipe: Dict[str, Any]) -> bool:
        """Validate extracted recipe data"""
        required_fields = ['name', 'ingredients_needed', 'instructions']
        
        if not all(field in recipe for field in required_fields):
            return False
        
        # Check that we have meaningful data
        if not recipe['name'] or not recipe['ingredients_needed'] or not recipe['instructions']:
            return False
        
        # Ensure ingredients and instructions are lists
        if not isinstance(recipe['ingredients_needed'], list) or not isinstance(recipe['instructions'], list):
            return False
        
        return True

    def _get_mock_recipe_extraction(self, source_url: str) -> Dict[str, Any]:
        """Return mock recipe for testing"""
        return {
            "name": "Mock Extracted Recipe",
            "description": "A test recipe extracted from URL for testing purposes",
            "prep_time": 25,
            "difficulty": "Easy",
            "servings": 4,
            "ingredients_needed": [
                {"name": "test ingredient", "quantity": "2", "unit": "cups", "have_in_pantry": False}
            ],
            "instructions": ["Test instruction 1", "Test instruction 2"],
            "tags": ["test", "extracted", "mock"],
            "nutrition_notes": "Mock nutritional information",
            "pantry_usage_score": 0,
            "ai_generated": True,
            "ai_provider": "mock"
        }

    async def get_ai_response(self, prompt: str, provider: AIProvider = "all") -> str:
        """
        Get a generic AI response for a given prompt
        Used for book recommendations and other general AI tasks
        """
        try:
            # Prioritize Groq as requested
            if provider == "all" or provider == "groq":
                if self.groq_client:
                    try:
                        logger.info("🤖 Using Groq for AI response")
                        return await self._get_groq_response(prompt)
                    except Exception as e:
                        logger.error(f"Groq failed: {e}")
                        if provider == "groq":
                            raise
            
            # Fallback to Perplexity
            if provider == "all" or provider == "perplexity":
                if self.perplexity_api_key:
                    try:
                        logger.info("🤖 Using Perplexity for AI response")
                        return await self._get_perplexity_response(prompt)
                    except Exception as e:
                        logger.error(f"Perplexity failed: {e}")
                        if provider == "perplexity":
                            raise
            
            # Fallback to Claude
            if provider == "all" or provider == "claude":
                if self.claude_client:
                    try:
                        logger.info("🤖 Using Claude for AI response")
                        return await self._get_claude_response(prompt)
                    except Exception as e:
                        logger.error(f"Claude failed: {e}")
                        if provider == "claude":
                            raise
            
            # If no provider is available, raise an error
            raise ValueError("No AI provider available for generating response")
            
        except Exception as e:
            logger.error(f"❌ Error getting AI response: {e}")
            raise

    async def _get_perplexity_response(self, prompt: str) -> str:
        """Get response from Perplexity API"""
        try:
            logger.info("Getting response from Perplexity...")
            url = "https://api.perplexity.ai/chat/completions"
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.7
            }
            
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=60.0)
                response.raise_for_status()
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                logger.info(f"Perplexity response received, length: {len(content)}")
                return content
                
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise

    async def _get_claude_response(self, prompt: str) -> str:
        """Get response from Claude API"""
        try:
            logger.info("Getting response from Claude...")
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            logger.info(f"Claude response received, length: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def _get_groq_response(self, prompt: str) -> str:
        """Get response from Groq API"""
        try:
            logger.info("Getting response from Groq...")
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            logger.info(f"Groq response received, length: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    async def extract_book_details(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract book details using AI services"""
        try:
            logger.info(f"🤖 Extracting book details for: {title} by {author or 'Unknown Author'}")
            
            # Return mock data in testing mode
            if self.is_testing:
                logger.info("Testing mode: returning mock book details")
                return self._get_mock_book_details(title, author)
            
            # Try providers in order of preference
            providers = ["perplexity", "claude", "groq"]
            
            for provider in providers:
                try:
                    logger.info(f"🔄 Trying book details extraction with {provider}")
                    
                    if provider == "perplexity" and self.perplexity_key:
                        result = await self._extract_book_details_perplexity(title, author)
                    elif provider == "claude" and self.claude_client:
                        result = await self._extract_book_details_claude(title, author)
                    elif provider == "groq" and self.groq_client:
                        result = await self._extract_book_details_groq(title, author)
                    else:
                        continue
                    
                    if result and self._validate_extracted_book_details(result):
                        logger.info(f"✅ Book details extracted successfully with {provider}")
                        result['ai_provider'] = provider
                        return result
                    else:
                        logger.warning(f"❌ Book details extraction failed with {provider}")
                        
                except Exception as e:
                    logger.error(f"{provider.title()} book details extraction error: {e}")
                    logger.warning(f"❌ Book details extraction failed with {provider}: {e}")
                    continue
            
            logger.error("❌ All providers failed for book details extraction")
            return None
            
        except Exception as e:
            logger.error(f"❌ Book details extraction failed: {e}")
            return None

    async def _extract_book_details_perplexity(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract book details using Perplexity AI"""
        prompt = self._build_book_details_prompt(title, author)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return self._parse_book_details_response(content)

    async def _extract_book_details_claude(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract book details using Claude AI"""
        prompt = self._build_book_details_prompt(title, author)
        
        message = self.claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_book_details_response(message.content[0].text)

    async def _extract_book_details_groq(self, title: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract book details using Groq"""
        prompt = self._build_book_details_prompt(title, author)
        
        chat_completion = self.groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        content = chat_completion.choices[0].message.content
        return self._parse_book_details_response(content)

    def _build_book_details_prompt(self, title: str, author: Optional[str] = None) -> str:
        """Build structured prompt for book details extraction"""
        author_part = f" by {author}" if author else ""
        
        return f"""
Extract detailed information about the book "{title}"{author_part}. 

Return the information in this exact JSON format:
{{
    "title": "Full book title",
    "author": "Author name",
    "publication_year": 2023,
    "pages": 300,
    "genre": "Fiction",
    "description": "Brief book description/synopsis",
    "isbn": "ISBN number if available",
    "confidence": {{
        "publication_year": 0.95,
        "pages": 0.85,
        "genre": 0.90,
        "description": 0.88
    }}
}}

Guidelines:
- If information is not available, use null
- For confidence, use 0.0-1.0 scale (1.0 = very certain)
- Keep description under 500 characters
- Use the most common/recognized title and author name
- For genre, use broad categories like "Fiction", "Non-fiction", "Mystery", "Science Fiction", etc.
- Only include ISBN if you're confident it's correct

Book: "{title}"{author_part}
"""

    def _parse_book_details_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse book details from AI response"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in book details response")
                return None
            
            json_str = json_match.group()
            book_data = json.loads(json_str)
            
            # Validate and clean the data
            cleaned_data = {
                'title': str(book_data.get('title', '')).strip(),
                'author': str(book_data.get('author', '')).strip(),
                'publication_year': book_data.get('publication_year'),
                'pages': book_data.get('pages'),
                'genre': str(book_data.get('genre', '')).strip() if book_data.get('genre') else None,
                'description': str(book_data.get('description', '')).strip() if book_data.get('description') else None,
                'isbn': str(book_data.get('isbn', '')).strip() if book_data.get('isbn') else None,
                'confidence': book_data.get('confidence', {})
            }
            
            # Validate publication year
            if cleaned_data['publication_year']:
                try:
                    year = int(cleaned_data['publication_year'])
                    if year < 0 or year > 3000:
                        cleaned_data['publication_year'] = None
                    else:
                        cleaned_data['publication_year'] = year
                except (ValueError, TypeError):
                    cleaned_data['publication_year'] = None
            
            # Validate pages
            if cleaned_data['pages']:
                try:
                    pages = int(cleaned_data['pages'])
                    if pages <= 0:
                        cleaned_data['pages'] = None
                    else:
                        cleaned_data['pages'] = pages
                except (ValueError, TypeError):
                    cleaned_data['pages'] = None
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error parsing book details response: {e}")
            return None

    def _validate_extracted_book_details(self, book_details: Dict[str, Any]) -> bool:
        """Validate extracted book details"""
        if not book_details.get('title') or not book_details.get('author'):
            return False
        
        # At least one meaningful piece of information should be present
        meaningful_fields = ['publication_year', 'pages', 'genre', 'description']
        has_meaningful_data = any(book_details.get(field) for field in meaningful_fields)
        
        return has_meaningful_data

    def _get_mock_book_details(self, title: str, author: Optional[str] = None) -> Dict[str, Any]:
        """Return mock book details for testing"""
        return {
            "title": title,
            "author": author or "Mock Author",
            "publication_year": 2020,
            "pages": 250,
            "genre": "Fiction",
            "description": f"This is a mock description for the book '{title}' used for testing purposes.",
            "isbn": "9780123456789",
            "confidence": {
                "publication_year": 0.95,
                "pages": 0.85,
                "genre": 0.90,
                "description": 0.88
            },
            "ai_provider": "mock"
        }

# Global instance
ai_service = AIService()