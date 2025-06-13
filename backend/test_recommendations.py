import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from claude_service import ClaudeService


class TestClaudeService:
    
    @pytest.fixture
    def claude_service(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            return ClaudeService()
    
    @pytest.fixture
    def sample_family_members(self):
        return [
            {
                'id': '1',
                'name': 'John',
                'age': 35,
                'dietary_restrictions': ['vegetarian'],
                'preferences': {'spice_level': 'mild'}
            }
        ]
    
    @pytest.fixture
    def sample_pantry_items(self):
        return [
            {
                'quantity': 2,
                'expiration_date': '2024-12-31',
                'ingredient': {
                    'id': '1',
                    'name': 'Chicken Breast',
                    'category': 'Meat',
                    'unit': 'pound'
                }
            },
            {
                'quantity': 1,
                'expiration_date': '2024-12-31',
                'ingredient': {
                    'id': '2',
                    'name': 'Rice',
                    'category': 'Grain',
                    'unit': 'cup'
                }
            }
        ]
    
    def test_claude_service_initialization_with_api_key(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeService()
            assert service.is_available() == True
    
    def test_claude_service_initialization_without_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeService()
            assert service.is_available() == False
    
    @pytest.mark.asyncio
    async def test_get_meal_recommendations_with_api_key(self, claude_service, sample_family_members, sample_pantry_items):
        # Mock the Claude API response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
            "recommendations": [
                {
                    "name": "Test Recipe",
                    "description": "A test recipe",
                    "prep_time": 30,
                    "difficulty": "Easy",
                    "servings": 4,
                    "ingredients_needed": [
                        {
                            "name": "test ingredient",
                            "quantity": "1",
                            "unit": "cup",
                            "have_in_pantry": true
                        }
                    ],
                    "instructions": ["Step 1"],
                    "tags": ["test"],
                    "nutrition_notes": "Healthy",
                    "pantry_usage_score": 80
                }
            ]
        }
        '''
        
        with patch.object(claude_service.client, 'messages') as mock_messages:
            mock_messages.create = Mock(return_value=mock_response)
            
            recommendations = await claude_service.get_meal_recommendations(
                family_members=sample_family_members,
                pantry_items=sample_pantry_items,
                num_recommendations=1
            )
            
            assert len(recommendations) == 1
            assert recommendations[0]['name'] == 'Test Recipe'
            assert recommendations[0]['ai_generated'] == True
            assert 'AI-Generated' in recommendations[0]['tags']
    
    @pytest.mark.asyncio
    async def test_get_meal_recommendations_without_api_key(self, sample_family_members, sample_pantry_items):
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeService()
            
            recommendations = await service.get_meal_recommendations(
                family_members=sample_family_members,
                pantry_items=sample_pantry_items,
                num_recommendations=3
            )
            
            # Should return fallback recommendations
            assert len(recommendations) == 3
            assert recommendations[0]['name'] == 'Simple Pasta with Garlic'
            assert recommendations[0]['ai_generated'] == False
            assert 'Fallback' in recommendations[0]['tags']
    
    @pytest.mark.asyncio
    async def test_get_meal_recommendations_api_error(self, claude_service, sample_family_members, sample_pantry_items):
        with patch.object(claude_service.client, 'messages') as mock_messages:
            mock_messages.create = Mock(side_effect=Exception("API Error"))
            
            recommendations = await claude_service.get_meal_recommendations(
                family_members=sample_family_members,
                pantry_items=sample_pantry_items,
                num_recommendations=1
            )
            
            # Should return fallback recommendations on error
            assert len(recommendations) == 3
            assert recommendations[0]['ai_generated'] == False
    
    def test_build_recommendation_prompt(self, claude_service, sample_family_members, sample_pantry_items):
        prompt = claude_service._build_recommendation_prompt(
            family_members=sample_family_members,
            pantry_items=sample_pantry_items,
            preferences=None,
            num_recommendations=3
        )
        
        assert 'John' in prompt
        assert 'vegetarian' in prompt
        assert 'Chicken Breast' in prompt
        assert 'Rice' in prompt
        assert '3 personalized meal recommendations' in prompt
    
    def test_parse_claude_response_valid_json(self, claude_service):
        valid_response = '''
        {
            "recommendations": [
                {
                    "name": "Test Recipe",
                    "description": "Test description",
                    "prep_time": 30,
                    "difficulty": "Easy",
                    "servings": 4,
                    "ingredients_needed": [],
                    "instructions": [],
                    "tags": [],
                    "nutrition_notes": "Test",
                    "pantry_usage_score": 80
                }
            ]
        }
        '''
        
        recommendations = claude_service._parse_claude_response(valid_response)
        assert len(recommendations) == 1
        assert recommendations[0]['name'] == 'Test Recipe'
    
    def test_parse_claude_response_invalid_json(self, claude_service):
        invalid_response = "This is not JSON"
        
        recommendations = claude_service._parse_claude_response(invalid_response)
        
        # Should return fallback recommendations
        assert len(recommendations) == 3
        assert recommendations[0]['name'] == 'Simple Pasta with Garlic'
    
    def test_validate_recommendation_valid(self, claude_service):
        valid_rec = {
            'name': 'Test',
            'description': 'Test desc',
            'prep_time': 30,
            'difficulty': 'Easy',
            'servings': 4
        }
        
        assert claude_service._validate_recommendation(valid_rec) == True
    
    def test_validate_recommendation_missing_fields(self, claude_service):
        invalid_rec = {
            'name': 'Test'
            # Missing required fields
        }
        
        assert claude_service._validate_recommendation(invalid_rec) == False


if __name__ == "__main__":
    pytest.main([__file__])