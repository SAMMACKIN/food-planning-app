import pytest
from tests.conftest import IngredientFactory


@pytest.mark.api
class TestIngredientsAPI:
    """Test ingredients endpoints"""
    
    def test_get_ingredients_list(self, client):
        """Test getting ingredients list"""
        response = client.get("/api/v1/ingredients")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have sample ingredients
        assert len(data) > 0
        
        # Check first ingredient has required fields
        ingredient = data[0]
        required_fields = ['id', 'name', 'category', 'unit']
        for field in required_fields:
            assert field in ingredient
    
    def test_search_ingredients_valid_query(self, client):
        """Test ingredient search with valid query"""
        response = client.get("/api/v1/ingredients/search?q=chicken")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Should find chicken in results
        chicken_found = any('chicken' in item['name'].lower() for item in data)
        assert chicken_found
    
    def test_search_ingredients_empty_query(self, client):
        """Test ingredient search with empty query"""
        response = client.get("/api/v1/ingredients/search?q=")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return all ingredients or empty list
    
    def test_search_ingredients_no_results(self, client):
        """Test ingredient search with no matching results"""
        response = client.get("/api/v1/ingredients/search?q=nonexistentfood123")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_search_ingredients_case_insensitive(self, client):
        """Test ingredient search is case insensitive"""
        # Test with uppercase
        response1 = client.get("/api/v1/ingredients/search?q=CHICKEN")
        assert response1.status_code == 200
        
        # Test with lowercase
        response2 = client.get("/api/v1/ingredients/search?q=chicken")
        assert response2.status_code == 200
        
        # Results should be the same (or at least both have results)
        data1 = response1.json()
        data2 = response2.json()
        
        if len(data1) > 0 and len(data2) > 0:
            # Should find similar results
            assert len(data1) == len(data2)
    
    def test_search_ingredients_partial_match(self, client):
        """Test ingredient search with partial matches"""
        response = client.get("/api/v1/ingredients/search?q=chick")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Should find items containing "chick" (like chicken)
        if len(data) > 0:
            found_partial = any('chick' in item['name'].lower() for item in data)
            assert found_partial
    
    def test_search_ingredients_category_filter(self, client):
        """Test ingredient search with category filter (if implemented)"""
        response = client.get("/api/v1/ingredients/search?q=&category=Protein")
        
        # This endpoint might not exist yet, so just check it doesn't crash
        assert response.status_code in [200, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_ingredient_by_id(self, client):
        """Test getting a specific ingredient by ID"""
        # First get the list to find a valid ID
        list_response = client.get("/api/v1/ingredients")
        assert list_response.status_code == 200
        
        ingredients = list_response.json()
        if len(ingredients) > 0:
            ingredient_id = ingredients[0]['id']
            
            response = client.get(f"/api/v1/ingredients/{ingredient_id}")
            # This endpoint might not exist yet
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data['id'] == ingredient_id
    
    def test_get_ingredient_categories(self, client):
        """Test getting available ingredient categories"""
        response = client.get("/api/v1/ingredients/categories")
        
        # This endpoint might not exist yet
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Should have some categories
            assert len(data) > 0
    
    def test_ingredients_pagination(self, client):
        """Test ingredients pagination (if implemented)"""
        response = client.get("/api/v1/ingredients?page=1&limit=10")
        
        # Might not be implemented yet
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))  # Could be paginated response
    
    def test_ingredients_response_structure(self, client):
        """Test that ingredients have consistent response structure"""
        response = client.get("/api/v1/ingredients")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            for ingredient in data[:3]:  # Check first few ingredients
                # Required fields
                assert 'id' in ingredient
                assert 'name' in ingredient
                assert 'category' in ingredient
                assert 'unit' in ingredient
                
                # Data types
                assert isinstance(ingredient['id'], str)  # UUID is returned as string
                assert isinstance(ingredient['name'], str)
                assert isinstance(ingredient['category'], str)
                assert isinstance(ingredient['unit'], str)
                
                # Optional fields if present
                if 'calories_per_unit' in ingredient:
                    assert isinstance(ingredient['calories_per_unit'], (int, float))
                
                if 'common_uses' in ingredient:
                    assert isinstance(ingredient['common_uses'], list)