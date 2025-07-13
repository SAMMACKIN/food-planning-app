"""
Recipe URL Import Service
Handles web scraping and AI-powered recipe extraction from URLs
"""
import re
import json
import httpx
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import asyncio

from ..ai_service import ai_service

logger = logging.getLogger(__name__)

class RecipeURLService:
    def __init__(self):
        self.timeout = 30.0
        self.max_content_size = 1024 * 1024  # 1MB limit
        
        # Common recipe structured data selectors
        self.structured_selectors = [
            'script[type="application/ld+json"]',
            '[itemtype*="Recipe"]',
            '[itemtype*="recipe"]'
        ]
        
        # Common recipe content selectors for fallback
        self.content_selectors = {
            'title': ['h1', '.recipe-title', '.recipe-name', '[itemprop="name"]', 'title'],
            'description': ['.recipe-description', '[itemprop="description"]', '.recipe-summary'],
            'ingredients': ['.recipe-ingredients', '[itemprop="recipeIngredient"]', '.ingredients-list', '.ingredient'],
            'instructions': ['.recipe-instructions', '[itemprop="recipeInstructions"]', '.instructions', '.method', '.directions'],
            'prep_time': ['[itemprop="prepTime"]', '.prep-time', '.preparation-time'],
            'cook_time': ['[itemprop="cookTime"]', '.cook-time', '.cooking-time'],
            'total_time': ['[itemprop="totalTime"]', '.total-time'],
            'servings': ['[itemprop="recipeYield"]', '.servings', '.yield', '.portions'],
            'image': ['[itemprop="image"]', '.recipe-image img', '.recipe-photo img', 'meta[property="og:image"]']
        }

    async def extract_recipe_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract recipe data from a URL using web scraping and AI
        """
        try:
            logger.info(f"🌐 Starting recipe extraction from: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL provided")
            
            # Fetch webpage content
            html_content = await self._fetch_webpage(url)
            if not html_content:
                return None
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try structured data extraction first
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                logger.info("✅ Found structured recipe data (JSON-LD or microdata)")
                recipe_data = await self._process_structured_data(structured_data, url)
                if recipe_data:
                    return recipe_data
            
            # Fallback to AI-powered extraction
            logger.info("🤖 Using AI to extract recipe from HTML content")
            return await self._ai_extract_recipe(soup, url)
            
        except Exception as e:
            logger.error(f"❌ Recipe extraction failed for {url}: {e}")
            return None

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format and domain"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False

    async def _fetch_webpage(self, url: str) -> Optional[str]:
        """Fetch webpage content with proper headers and error handling"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Check content size
                content_length = len(response.content)
                if content_length > self.max_content_size:
                    logger.warning(f"Content too large: {content_length} bytes")
                    return None
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    logger.warning(f"Not HTML content: {content_type}")
                    return None
                
                logger.info(f"✅ Successfully fetched {content_length} bytes from {url}")
                return response.text
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Timeout fetching {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"📡 HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {e}")
            return None

    def _extract_structured_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract structured data (JSON-LD, microdata) from HTML"""
        try:
            # Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle single object or array
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        # Look for Recipe schema
                        if self._is_recipe_schema(item):
                            logger.info("🎯 Found Recipe schema in JSON-LD")
                            return item
                            
                except json.JSONDecodeError:
                    continue
                    
            # Look for microdata
            recipe_microdata = soup.find(attrs={'itemtype': lambda x: x and 'Recipe' in x})
            if recipe_microdata:
                logger.info("🎯 Found Recipe microdata")
                return self._extract_microdata(recipe_microdata)
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting structured data: {e}")
            return None

    def _is_recipe_schema(self, item: Dict[str, Any]) -> bool:
        """Check if item is a Recipe schema"""
        item_type = item.get('@type', '')
        if isinstance(item_type, list):
            return any('Recipe' in t for t in item_type)
        return 'Recipe' in str(item_type)

    def _extract_microdata(self, element) -> Dict[str, Any]:
        """Extract recipe data from microdata element"""
        # This is a simplified microdata extractor
        # In a full implementation, you'd properly parse microdata properties
        return {
            'name': self._get_microdata_property(element, 'name'),
            'description': self._get_microdata_property(element, 'description'),
            'recipeIngredient': self._get_microdata_properties(element, 'recipeIngredient'),
            'recipeInstructions': self._get_microdata_properties(element, 'recipeInstructions'),
        }

    def _get_microdata_property(self, element, prop_name: str) -> Optional[str]:
        """Get single microdata property value"""
        prop_element = element.find(attrs={'itemprop': prop_name})
        return prop_element.get_text(strip=True) if prop_element else None

    def _get_microdata_properties(self, element, prop_name: str) -> list:
        """Get multiple microdata property values"""
        prop_elements = element.find_all(attrs={'itemprop': prop_name})
        return [el.get_text(strip=True) for el in prop_elements if el.get_text(strip=True)]

    async def _process_structured_data(self, data: Dict[str, Any], source_url: str) -> Optional[Dict[str, Any]]:
        """Process structured data into recipe format"""
        try:
            recipe = {
                'name': self._extract_text(data.get('name', '')),
                'description': self._extract_text(data.get('description', '')),
                'source': source_url,
                'ai_generated': False,  # This is structured data, not AI generated
                'ai_provider': None
            }
            
            # Extract ingredients
            ingredients = []
            recipe_ingredients = data.get('recipeIngredient', [])
            if isinstance(recipe_ingredients, list):
                for ingredient in recipe_ingredients:
                    parsed = self._parse_ingredient(self._extract_text(ingredient))
                    if parsed:
                        ingredients.append(parsed)
            
            recipe['ingredients_needed'] = ingredients
            
            # Extract instructions
            instructions = []
            recipe_instructions = data.get('recipeInstructions', [])
            if isinstance(recipe_instructions, list):
                for instruction in recipe_instructions:
                    if isinstance(instruction, dict):
                        text = instruction.get('text', '')
                    else:
                        text = str(instruction)
                    
                    text = self._extract_text(text)
                    if text:
                        instructions.append(text)
            
            recipe['instructions'] = instructions
            
            # Extract timing and servings
            prep_time = self._parse_duration(data.get('prepTime'))
            cook_time = self._parse_duration(data.get('cookTime'))
            total_time = self._parse_duration(data.get('totalTime'))
            
            # Use total time, or sum prep + cook time
            if total_time:
                recipe['prep_time'] = total_time
            elif prep_time and cook_time:
                recipe['prep_time'] = prep_time + cook_time
            elif prep_time:
                recipe['prep_time'] = prep_time
            else:
                recipe['prep_time'] = 30  # Default
            
            # Extract servings
            recipe_yield = data.get('recipeYield')
            if recipe_yield:
                servings = self._parse_servings(recipe_yield)
                recipe['servings'] = servings if servings else 4
            else:
                recipe['servings'] = 4
            
            # Set default values
            recipe['difficulty'] = 'Medium'
            recipe['tags'] = ['imported', 'web-recipe']
            recipe['nutrition_notes'] = ''
            recipe['pantry_usage_score'] = 0
            
            # Validate we have minimum required data
            if recipe['name'] and recipe['ingredients_needed'] and recipe['instructions']:
                logger.info(f"✅ Successfully processed structured data: {recipe['name']}")
                return recipe
            else:
                logger.warning("❌ Structured data missing required fields")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing structured data: {e}")
            return None

    async def _ai_extract_recipe(self, soup: BeautifulSoup, source_url: str) -> Optional[Dict[str, Any]]:
        """Use AI to extract recipe from HTML content"""
        try:
            # Extract text content from HTML
            text_content = self._extract_clean_text(soup)
            
            if len(text_content) < 100:
                logger.warning("❌ Insufficient content for AI extraction")
                return None
            
            # Use AI service to extract recipe
            recipe_data = await ai_service.extract_recipe_from_content(text_content, source_url)
            
            if recipe_data:
                # Add metadata
                recipe_data['source'] = source_url
                recipe_data['ai_generated'] = True
                recipe_data['tags'] = recipe_data.get('tags', []) + ['imported', 'ai-extracted']
                
                logger.info(f"✅ AI extracted recipe: {recipe_data.get('name', 'Unknown')}")
                return recipe_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            return None

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'comment']):
            element.decompose()
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content|main|recipe'))
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Limit length for AI processing
        max_length = 8000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text

    def _extract_text(self, value) -> str:
        """Extract text from various formats"""
        if isinstance(value, dict):
            return value.get('text', '') or value.get('@value', '') or str(value)
        elif isinstance(value, list):
            return ' '.join(str(item) for item in value)
        else:
            return str(value).strip()

    def _parse_ingredient(self, ingredient_text: str) -> Optional[Dict[str, Any]]:
        """Parse ingredient text into structured format"""
        if not ingredient_text:
            return None
        
        # Simple ingredient parsing - could be enhanced with NLP
        # Look for patterns like "2 cups flour" or "1 lb chicken"
        
        # Clean the text
        text = ingredient_text.strip()
        
        # Try to extract quantity and unit using regex
        patterns = [
            r'^(\d+(?:\.\d+)?)\s*(\w+)\s+(.+)$',  # "2 cups flour"
            r'^(\d+(?:\.\d+)?)\s+(.+)$',          # "2 eggs"
            r'^(.+)$'                             # "salt to taste"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:  # quantity, unit, name
                    return {
                        'quantity': groups[0],
                        'unit': groups[1],
                        'name': groups[2],
                        'have_in_pantry': False
                    }
                elif len(groups) == 2:  # quantity, name (no unit)
                    return {
                        'quantity': groups[0],
                        'unit': '',
                        'name': groups[1],
                        'have_in_pantry': False
                    }
                else:  # just name
                    return {
                        'quantity': '',
                        'unit': '',
                        'name': groups[0],
                        'have_in_pantry': False
                    }
        
        # Fallback - treat entire text as ingredient name
        return {
            'quantity': '',
            'unit': '',
            'name': text,
            'have_in_pantry': False
        }

    def _parse_duration(self, duration) -> Optional[int]:
        """Parse duration string into minutes"""
        if not duration:
            return None
        
        duration_str = str(duration).lower()
        
        # Handle ISO 8601 duration (PT30M)
        if duration_str.startswith('pt'):
            hours_match = re.search(r'(\d+)h', duration_str)
            minutes_match = re.search(r'(\d+)m', duration_str)
            
            total_minutes = 0
            if hours_match:
                total_minutes += int(hours_match.group(1)) * 60
            if minutes_match:
                total_minutes += int(minutes_match.group(1))
            
            return total_minutes if total_minutes > 0 else None
        
        # Handle common text formats
        minutes_match = re.search(r'(\d+)\s*(?:min|minute|minutes)', duration_str)
        if minutes_match:
            return int(minutes_match.group(1))
        
        hours_match = re.search(r'(\d+)\s*(?:hour|hours|hr|hrs)', duration_str)
        if hours_match:
            return int(hours_match.group(1)) * 60
        
        # Look for just numbers
        number_match = re.search(r'(\d+)', duration_str)
        if number_match:
            return int(number_match.group(1))
        
        return None

    def _parse_servings(self, servings) -> Optional[int]:
        """Parse servings from various formats"""
        if not servings:
            return None
        
        servings_str = str(servings).lower()
        
        # Look for numbers
        number_match = re.search(r'(\d+)', servings_str)
        if number_match:
            return int(number_match.group(1))
        
        return None


# Global instance
recipe_url_service = RecipeURLService()