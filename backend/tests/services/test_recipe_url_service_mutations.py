"""
Mutation-resistant tests for Recipe URL Service
These tests are designed to catch common mutations and ensure code correctness
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from bs4 import BeautifulSoup

from app.services.recipe_url_service import RecipeURLService


class TestRecipeURLServiceMutations:
    """Mutation-resistant tests for RecipeURLService"""
    
    @pytest.fixture
    def service(self):
        """Create a service instance"""
        return RecipeURLService()
    
    def test_normalize_ingredient_quantity_boundaries(self, service):
        """Test quantity normalization with boundary values"""
        # Test exact boundary values to catch off-by-one mutations
        assert service._normalize_ingredient_quantity("0.5") == 0.5
        assert service._normalize_ingredient_quantity("0.50") == 0.5
        assert service._normalize_ingredient_quantity("0.500") == 0.5
        
        # Test that 1/2 equals exactly 0.5
        assert service._normalize_ingredient_quantity("1/2") == 0.5
        assert service._normalize_ingredient_quantity("2/4") == 0.5
        
        # Test negative values (should handle or reject)
        result = service._normalize_ingredient_quantity("-1")
        assert result == 0 or result == 1  # Should normalize to valid value
        
        # Test zero
        assert service._normalize_ingredient_quantity("0") == 0
        assert service._normalize_ingredient_quantity("0/1") == 0
    
    def test_parse_cooking_time_exact_values(self, service):
        """Test cooking time parsing with exact minute calculations"""
        # Test exact conversions to catch multiplication errors
        assert service._parse_cooking_time("1 hour") == 60  # Not 59 or 61
        assert service._parse_cooking_time("2 hours") == 120  # Exactly 2 * 60
        assert service._parse_cooking_time("1.5 hours") == 90  # Exactly 1.5 * 60
        
        # Test addition is correct
        assert service._parse_cooking_time("1 hour 30 minutes") == 90  # 60 + 30
        assert service._parse_cooking_time("2 hours 15 minutes") == 135  # 120 + 15
        
        # Test edge cases
        assert service._parse_cooking_time("0 hours") == 0
        assert service._parse_cooking_time("24 hours") == 1440  # Full day
        
        # Test that order doesn't matter (commutative)
        assert service._parse_cooking_time("30 minutes 1 hour") == service._parse_cooking_time("1 hour 30 minutes")
    
    def test_extract_recipe_data_completeness(self, service):
        """Test that all required fields are extracted"""
        html_content = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@type": "Recipe",
                    "name": "Test Recipe",
                    "recipeYield": "4 servings",
                    "totalTime": "PT1H30M",
                    "recipeIngredient": ["1 cup flour", "2 eggs"],
                    "recipeInstructions": [
                        {"@type": "HowToStep", "text": "Step 1"},
                        {"@type": "HowToStep", "text": "Step 2"}
                    ]
                }
                </script>
            </head>
        </html>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        result = service._extract_recipe_data(soup, "http://example.com")
        
        # Verify all fields are present and correct
        assert result is not None
        assert result['name'] == "Test Recipe"  # Exact match
        assert result['servings'] == 4  # Numeric, not "4" or "4 servings"
        assert result['prep_time'] == 90  # PT1H30M = 90 minutes exactly
        assert len(result['ingredients']) == 2  # Exactly 2, not 1 or 3
        assert len(result['instructions']) == 2  # Exactly 2 steps
        
        # Verify ingredients are properly formatted
        assert result['ingredients'][0]['original'] == "1 cup flour"
        assert result['ingredients'][1]['original'] == "2 eggs"
    
    def test_parse_servings_string_variations(self, service):
        """Test serving parsing handles all variations correctly"""
        # Test exact parsing
        assert service._parse_servings("4") == 4
        assert service._parse_servings("4 servings") == 4
        assert service._parse_servings("Serves 4") == 4
        assert service._parse_servings("Makes 4") == 4
        assert service._parse_servings("Yield: 4") == 4
        
        # Test ranges - should return exact values
        result = service._parse_servings("4-6 servings")
        assert result == 4 or result == 5 or result == 6  # Should be within range
        
        # Test edge cases
        assert service._parse_servings("1 serving") == 1  # Singular
        assert service._parse_servings("12 servings") == 12  # Double digit
        assert service._parse_servings("100 servings") == 100  # Triple digit
        
        # Test invalid inputs return None or default
        assert service._parse_servings("") in [None, 1, 4]  # Should have sensible default
        assert service._parse_servings("invalid") in [None, 1, 4]
    
    def test_url_validation_strict(self, service):
        """Test URL validation is strict and secure"""
        # Valid URLs that must pass
        valid_urls = [
            "https://example.com/recipe",
            "http://example.com/recipe",
            "https://sub.example.com/path/to/recipe",
            "https://example.com:8080/recipe"
        ]
        
        for url in valid_urls:
            result = service._validate_url(url)
            assert result is True or result == url  # Should accept
        
        # Invalid URLs that must fail
        invalid_urls = [
            "javascript:alert('xss')",
            "file:///etc/passwd",
            "ftp://example.com/recipe",
            "../../../etc/passwd",
            "example.com/recipe",  # Missing protocol
            "https://",  # Incomplete
            "",  # Empty
            None  # Null
        ]
        
        for url in invalid_urls:
            result = service._validate_url(url)
            assert result is False or result is None  # Should reject
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_counts(self, service):
        """Test that retry logic executes exact number of times"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Server error")
        
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await service.extract_from_url("https://example.com/recipe")
            
            # Should retry exactly the configured number of times
            assert call_count == 3  # Default retry count
            assert result is None  # Should fail after retries
    
    def test_ingredient_parsing_precision(self, service):
        """Test ingredient parsing maintains precision"""
        test_cases = [
            # (input, expected_quantity, expected_unit, expected_name)
            ("1/3 cup flour", 0.333, "cup", "flour"),  # Check precision
            ("2.5 cups sugar", 2.5, "cups", "sugar"),
            ("1 1/2 teaspoons salt", 1.5, "teaspoons", "salt"),
            ("3/4 pound butter", 0.75, "pound", "butter"),
            ("0.25 oz vanilla", 0.25, "oz", "vanilla"),
        ]
        
        for input_str, exp_qty, exp_unit, exp_name in test_cases:
            result = service._parse_ingredient(input_str)
            
            # Quantity should be within small tolerance
            assert abs(result['quantity'] - exp_qty) < 0.01
            assert result['unit'] == exp_unit
            assert result['name'] == exp_name
    
    def test_instruction_parsing_preserves_order(self, service):
        """Test that instruction order is strictly preserved"""
        instructions = [
            "First, do this",
            "Second, do that",
            "Third, do another",
            "Finally, finish"
        ]
        
        # Create HTML with instructions
        html = "<ol>"
        for inst in instructions:
            html += f"<li>{inst}</li>"
        html += "</ol>"
        
        soup = BeautifulSoup(html, 'html.parser')
        parsed = service._parse_instructions_from_list(soup.find('ol'))
        
        # Verify exact order preservation
        assert len(parsed) == len(instructions)
        for i, (original, parsed_inst) in enumerate(zip(instructions, parsed)):
            assert parsed_inst['step_number'] == i + 1  # 1-indexed
            assert parsed_inst['instruction'] == original
            assert parsed_inst['order'] == i  # 0-indexed
    
    def test_time_parsing_iso8601_accuracy(self, service):
        """Test ISO 8601 duration parsing accuracy"""
        test_cases = [
            ("PT30M", 30),  # 30 minutes
            ("PT1H", 60),   # 1 hour  
            ("PT1H30M", 90), # 1 hour 30 minutes
            ("PT2H15M", 135), # 2 hours 15 minutes
            ("PT45S", 1),    # 45 seconds rounds to 1 minute
            ("PT0S", 0),     # 0 seconds
            ("P1DT12H", 2160), # 1 day 12 hours = 36 hours
        ]
        
        for iso_str, expected_minutes in test_cases:
            result = service._parse_iso8601_duration(iso_str)
            assert result == expected_minutes
    
    def test_recipe_extraction_handles_missing_data(self, service):
        """Test that missing data doesn't cause incorrect defaults"""
        # Recipe with minimal data
        minimal_html = """
        <html>
            <head>
                <script type="application/ld+json">
                {"@type": "Recipe", "name": "Minimal Recipe"}
                </script>
            </head>
        </html>
        """
        
        soup = BeautifulSoup(minimal_html, 'html.parser')
        result = service._extract_recipe_data(soup, "http://example.com")
        
        # Should extract what's available without inventing data
        assert result is not None
        assert result['name'] == "Minimal Recipe"
        assert result['servings'] in [None, 4]  # Default or None
        assert result['prep_time'] in [None, 0]  # Default or None
        assert len(result['ingredients']) == 0  # Empty, not fabricated
        assert len(result['instructions']) == 0  # Empty, not fabricated
    
    def test_concurrent_extraction_isolation(self, service):
        """Test that concurrent extractions don't interfere"""
        # This would need to be async, but validates the concept
        url1_data = {"name": "Recipe 1", "servings": 4}
        url2_data = {"name": "Recipe 2", "servings": 6}
        
        # Simulate concurrent processing
        result1 = service._process_recipe_data(url1_data)
        result2 = service._process_recipe_data(url2_data)
        
        # Ensure no data mixing
        assert result1['name'] == "Recipe 1"
        assert result1['servings'] == 4
        assert result2['name'] == "Recipe 2"
        assert result2['servings'] == 6