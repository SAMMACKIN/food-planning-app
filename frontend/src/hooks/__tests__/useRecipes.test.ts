import { renderHook, act, waitFor } from '@testing-library/react';
import { useRecipes } from '../useRecipes';
import { apiRequest } from '../../services/api';
import { useAuthStore } from '../../store/authStore';
import { Recipe, RecipeCreate, MealRecommendation, RecipeRating, RecipeRatingCreate } from '../../types';

// Mock dependencies
jest.mock('../../services/api');
jest.mock('../../store/authStore');

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  removeItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock console methods to suppress debug logs
const consoleMock = {
  log: jest.fn(),
  error: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });

const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('useRecipes', () => {
  const mockRecipe: Recipe = {
    id: '1',
    user_id: 'user1',
    name: 'Test Recipe',
    description: 'A test recipe',
    prep_time: 30,
    difficulty: 'medium',
    servings: 4,
    ingredients_needed: [
      { name: 'ingredient1', quantity: '1', unit: 'cup', have_in_pantry: false },
      { name: 'ingredient2', quantity: '2', unit: 'tbsp', have_in_pantry: true }
    ],
    instructions: ['Test instructions'],
    tags: ['dinner', 'healthy'],
    nutrition_notes: 'High protein',
    pantry_usage_score: 0.8,
    ai_generated: false,
    ai_provider: undefined,
    source: 'manual',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  const mockRecommendation: MealRecommendation = {
    name: 'Recommended Recipe',
    description: 'A recommended recipe',
    prep_time: 25,
    difficulty: 'easy',
    servings: 2,
    ingredients_needed: [
      { name: 'rec_ingredient1', quantity: '1', unit: 'piece', have_in_pantry: true }
    ],
    instructions: ['Recommendation instructions'],
    tags: ['lunch'],
    nutrition_notes: 'Balanced',
    pantry_usage_score: 0.9,
    ai_generated: true,
    ai_provider: 'claude'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('mock-token');
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      checkAuth: jest.fn(),
      clearError: jest.fn(),
      loading: false,
      error: null,
    });
    consoleMock.log.mockClear();
    consoleMock.error.mockClear();
  });

  describe('Initial State', () => {
    test('should initialize with correct default values', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        checkAuth: jest.fn(),
        clearError: jest.fn(),
        loading: false,
        error: null,
      });

      const { result } = renderHook(() => useRecipes());

      expect(result.current.savedRecipes).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    test('should auto-fetch recipes when authenticated and no recipes exist', async () => {
      mockApiRequest.mockResolvedValue([mockRecipe]);

      renderHook(() => useRecipes());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith('GET', '/recipes');
      });
    });

    test('should not auto-fetch when not authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        checkAuth: jest.fn(),
        clearError: jest.fn(),
        loading: false,
        error: null,
      });

      renderHook(() => useRecipes());

      expect(mockApiRequest).not.toHaveBeenCalled();
    });
  });

  describe('fetchSavedRecipes', () => {
    test('should fetch recipes successfully', async () => {
      mockApiRequest.mockResolvedValue([mockRecipe]);
      const { result } = renderHook(() => useRecipes());

      await act(async () => {
        await result.current.fetchSavedRecipes();
      });

      expect(result.current.savedRecipes).toEqual([mockRecipe]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/recipes');
    });

    test('should fetch recipes with search parameters', async () => {
      mockApiRequest.mockResolvedValue([mockRecipe]);
      const { result } = renderHook(() => useRecipes());

      await act(async () => {
        await result.current.fetchSavedRecipes('pasta', 'easy', 'dinner');
      });

      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/recipes?search=pasta&difficulty=easy&tags=dinner');
    });

    test('should handle authentication error', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      const { result } = renderHook(() => useRecipes());

      await act(async () => {
        await result.current.fetchSavedRecipes();
      });

      expect(result.current.error).toBe('Please log in to view your saved recipes');
      expect(mockApiRequest).not.toHaveBeenCalled();
    });

    test('should handle 401 error and clear tokens', async () => {
      const error = {
        response: { status: 401 },
        message: 'Unauthorized'
      };
      mockApiRequest.mockRejectedValue(error);
      const { result } = renderHook(() => useRecipes());

      await act(async () => {
        await result.current.fetchSavedRecipes();
      });

      expect(result.current.error).toBe('Authentication failed. Please log in again.');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    test('should handle different error types', async () => {
      const testCases = [
        { error: { response: { status: 404 }, message: 'Not Found' }, expectedMessage: 'Recipes endpoint not found. This might be a deployment issue.' },
        { error: { response: { status: 500 }, message: 'Server Error' }, expectedMessage: 'Server error. Please try again later.' },
        { error: { code: 'ECONNREFUSED', message: 'Connection refused' }, expectedMessage: 'Cannot connect to server. Please check your connection.' },
        { error: { response: { data: { detail: 'Custom error' } }, message: 'Custom' }, expectedMessage: 'Custom error' }
      ];

      for (const testCase of testCases) {
        mockApiRequest.mockRejectedValue(testCase.error);
        const { result } = renderHook(() => useRecipes());

        await act(async () => {
          await result.current.fetchSavedRecipes();
        });

        expect(result.current.error).toBe(testCase.expectedMessage);
      }
    });
  });

  describe('saveRecipe', () => {
    const mockRecipeCreate: RecipeCreate = {
      name: 'New Recipe',
      description: 'A new recipe',
      prep_time: 45,
      difficulty: 'hard',
      servings: 6,
      ingredients_needed: [
        { name: 'new_ingredient', quantity: '3', unit: 'oz', have_in_pantry: false }
      ],
      instructions: ['New instructions'],
      tags: ['dinner'],
      nutrition_notes: 'High fiber',
      pantry_usage_score: 0.7,
      ai_generated: false,
      source: 'manual'
    };

    test('should save recipe successfully', async () => {
      mockApiRequest.mockResolvedValue(mockRecipe);
      const { result } = renderHook(() => useRecipes());

      let savedRecipe: Recipe | null = null;
      await act(async () => {
        savedRecipe = await result.current.saveRecipe(mockRecipeCreate);
      });

      expect(savedRecipe).toEqual(mockRecipe);
      expect(result.current.savedRecipes).toEqual([mockRecipe]);
      expect(mockApiRequest).toHaveBeenCalledWith('POST', '/recipes', mockRecipeCreate);
    });

    test('should handle authentication error', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      const { result } = renderHook(() => useRecipes());

      let savedRecipe: Recipe | null = null;
      await act(async () => {
        savedRecipe = await result.current.saveRecipe(mockRecipeCreate);
      });

      expect(savedRecipe).toBe(null);
      expect(result.current.error).toBe('No authentication token found. Please log in again.');
      expect(mockApiRequest).not.toHaveBeenCalled();
    });

    test('should handle save errors', async () => {
      const error = { response: { status: 422 }, message: 'Validation error' };
      mockApiRequest.mockRejectedValue(error);
      const { result } = renderHook(() => useRecipes());

      let savedRecipe: Recipe | null = null;
      await act(async () => {
        savedRecipe = await result.current.saveRecipe(mockRecipeCreate);
      });

      expect(savedRecipe).toBe(null);
      expect(result.current.error).toBe('Invalid recipe data. Please check all fields.');
    });
  });

  describe('saveRecommendationAsRecipe', () => {
    test('should save recommendation as recipe', async () => {
      mockApiRequest.mockResolvedValue(mockRecipe);
      const { result } = renderHook(() => useRecipes());

      let savedRecipe: Recipe | null = null;
      await act(async () => {
        savedRecipe = await result.current.saveRecommendationAsRecipe(mockRecommendation);
      });

      expect(savedRecipe).toEqual(mockRecipe);
      expect(mockApiRequest).toHaveBeenCalledWith('POST', '/recipes', expect.objectContaining({
        name: mockRecommendation.name,
        source: 'recommendation',
        ai_generated: mockRecommendation.ai_generated
      }));
    });

    test('should return existing recipe if already saved', async () => {
      const existingRecipe = { ...mockRecipe, name: mockRecommendation.name, source: 'recommendation', ai_generated: true };
      
      // First load the existing recipe via fetch
      mockApiRequest.mockResolvedValue([existingRecipe]);
      const { result } = renderHook(() => useRecipes());

      await waitFor(() => {
        expect(result.current.savedRecipes).toHaveLength(1);
      });

      let savedRecipe: Recipe | null = null;
      await act(async () => {
        savedRecipe = await result.current.saveRecommendationAsRecipe(mockRecommendation);
      });

      expect(savedRecipe).toEqual(existingRecipe);
    });
  });

  describe('deleteRecipe', () => {
    test('should delete recipe successfully', async () => {
      // First load a recipe, then delete it
      mockApiRequest
        .mockResolvedValueOnce([mockRecipe]) // Initial fetch
        .mockResolvedValueOnce(undefined); // Delete call
      
      const { result } = renderHook(() => useRecipes());

      await waitFor(() => {
        expect(result.current.savedRecipes).toHaveLength(1);
      });

      let success = false;
      await act(async () => {
        success = await result.current.deleteRecipe(mockRecipe.id);
      });

      expect(success).toBe(true);
      expect(result.current.savedRecipes).toEqual([]);
      expect(mockApiRequest).toHaveBeenCalledWith('DELETE', `/recipes/${mockRecipe.id}`);
    });

    test('should handle delete error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Delete failed'));
      const { result } = renderHook(() => useRecipes());

      let success = true;
      await act(async () => {
        success = await result.current.deleteRecipe(mockRecipe.id);
      });

      expect(success).toBe(false);
      expect(result.current.error).toBe('Failed to delete recipe');
    });
  });

  describe('updateRecipe', () => {
    const updateData = { name: 'Updated Recipe Name' };

    test('should update recipe successfully', async () => {
      const updatedRecipe = { ...mockRecipe, name: 'Updated Recipe Name' };
      mockApiRequest
        .mockResolvedValueOnce([mockRecipe]) // Initial fetch
        .mockResolvedValueOnce(updatedRecipe); // Update call
      
      const { result } = renderHook(() => useRecipes());

      await waitFor(() => {
        expect(result.current.savedRecipes).toHaveLength(1);
      });

      let updated: Recipe | null = null;
      await act(async () => {
        updated = await result.current.updateRecipe(mockRecipe.id, updateData);
      });

      expect(updated).toEqual(updatedRecipe);
      expect(result.current.savedRecipes[0].name).toBe('Updated Recipe Name');
      expect(mockApiRequest).toHaveBeenCalledWith('PUT', `/recipes/${mockRecipe.id}`, updateData);
    });

    test('should handle update error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Update failed'));
      const { result } = renderHook(() => useRecipes());

      let updated: Recipe | null = null;
      await act(async () => {
        updated = await result.current.updateRecipe(mockRecipe.id, updateData);
      });

      expect(updated).toBe(null);
      expect(result.current.error).toBe('Failed to update recipe');
    });
  });

  describe('Recipe Rating Functions', () => {
    const mockRating: RecipeRating = {
      id: 'rating1',
      recipe_id: mockRecipe.id,
      user_id: 'user1',
      rating: 5,
      review_text: 'Great recipe!',
      would_make_again: true,
      cooking_notes: 'Easy to follow',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    const mockRatingCreate: RecipeRatingCreate = {
      rating: 5,
      review_text: 'Great recipe!',
      would_make_again: true,
      cooking_notes: 'Easy to follow'
    };

    test('should create recipe rating successfully', async () => {
      mockApiRequest.mockResolvedValue(mockRating);
      const { result } = renderHook(() => useRecipes());

      let rating: RecipeRating | null = null;
      await act(async () => {
        rating = await result.current.createRecipeRating(mockRecipe.id, mockRatingCreate);
      });

      expect(rating).toEqual(mockRating);
      expect(mockApiRequest).toHaveBeenCalledWith('POST', `/recipes/${mockRecipe.id}/ratings`, mockRatingCreate);
    });

    test('should handle rating creation errors', async () => {
      const error = { response: { status: 400, data: { detail: 'User has already rated this recipe' } }, message: 'Request failed' };
      mockApiRequest.mockRejectedValue(error);
      const { result } = renderHook(() => useRecipes());

      let rating: RecipeRating | null = null;
      await act(async () => {
        rating = await result.current.createRecipeRating(mockRecipe.id, mockRatingCreate);
      });

      expect(rating).toBe(null);
      expect(result.current.error).toBe('You have already rated this recipe. Use the update option to change your rating.');
    });

    test('should get recipe ratings successfully', async () => {
      mockApiRequest.mockResolvedValue([mockRating]);
      const { result } = renderHook(() => useRecipes());

      let ratings: RecipeRating[] = [];
      await act(async () => {
        ratings = await result.current.getRecipeRatings(mockRecipe.id);
      });

      expect(ratings).toEqual([mockRating]);
      expect(mockApiRequest).toHaveBeenCalledWith('GET', `/recipes/${mockRecipe.id}/ratings`);
    });

    test('should update recipe rating successfully', async () => {
      const updatedRating = { ...mockRating, rating: 4, review_text: 'Good recipe!' };
      mockApiRequest.mockResolvedValue(updatedRating);
      const { result } = renderHook(() => useRecipes());

      let rating: RecipeRating | null = null;
      await act(async () => {
        rating = await result.current.updateRecipeRating(mockRecipe.id, mockRating.id, { 
          rating: 4, 
          review_text: 'Good recipe!',
          would_make_again: true
        });
      });

      expect(rating).toEqual(updatedRating);
      expect(mockApiRequest).toHaveBeenCalledWith('PUT', `/recipes/${mockRecipe.id}/ratings/${mockRating.id}`, { 
        rating: 4, 
        review_text: 'Good recipe!',
        would_make_again: true
      });
    });

    test('should delete recipe rating successfully', async () => {
      mockApiRequest.mockResolvedValue(undefined);
      const { result } = renderHook(() => useRecipes());

      let success = false;
      await act(async () => {
        success = await result.current.deleteRecipeRating(mockRecipe.id, mockRating.id);
      });

      expect(success).toBe(true);
      expect(mockApiRequest).toHaveBeenCalledWith('DELETE', `/recipes/${mockRecipe.id}/ratings/${mockRating.id}`);
    });
  });

  describe('Meal Plan Functions', () => {
    test('should add recipe to meal plan successfully', async () => {
      mockApiRequest.mockResolvedValue(undefined);
      const { result } = renderHook(() => useRecipes());

      let success = false;
      await act(async () => {
        success = await result.current.addRecipeToMealPlan(mockRecipe.id, '2024-01-15', 'dinner');
      });

      expect(success).toBe(true);
      expect(mockApiRequest).toHaveBeenCalledWith('POST', `/recipes/${mockRecipe.id}/add-to-meal-plan?meal_date=2024-01-15&meal_type=dinner`);
    });

    test('should handle meal plan authentication error', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      const { result } = renderHook(() => useRecipes());

      let success = true;
      await act(async () => {
        success = await result.current.addRecipeToMealPlan(mockRecipe.id, '2024-01-15', 'dinner');
      });

      expect(success).toBe(false);
      expect(result.current.error).toBe('No authentication token found. Please log in again.');
      expect(mockApiRequest).not.toHaveBeenCalled();
    });

    test('should add recommendation to meal plan', async () => {
      // Ensure localStorage has token
      localStorageMock.getItem.mockReturnValue('mock-token');
      
      // Clear any existing state by mocking empty recipes initially
      mockApiRequest.mockResolvedValueOnce([]); // Initial fetch returns empty
      
      const { result } = renderHook(() => useRecipes());
      
      // Wait for initial fetch to complete
      await waitFor(() => {
        expect(result.current.savedRecipes).toEqual([]);
      });
      
      // Now mock the meal plan workflow
      mockApiRequest
        .mockResolvedValueOnce(mockRecipe) // saveRecommendationAsRecipe -> saveRecipe call
        .mockResolvedValueOnce(undefined); // addRecipeToMealPlan call

      let success = false;
      await act(async () => {
        success = await result.current.addRecommendationToMealPlan(mockRecommendation, '2024-01-15', 'lunch');
      });

      expect(success).toBe(true);
      // Should have 3 total calls: 1 initial fetch + 2 for meal plan workflow
      expect(mockApiRequest).toHaveBeenCalledTimes(3);
      
      // Check the specific API calls (after initial fetch)
      expect(mockApiRequest).toHaveBeenNthCalledWith(2, 'POST', '/recipes', expect.objectContaining({
        name: mockRecommendation.name,
        source: 'recommendation'
      }));
      expect(mockApiRequest).toHaveBeenNthCalledWith(3, 'POST', `/recipes/${mockRecipe.id}/add-to-meal-plan?meal_date=2024-01-15&meal_type=lunch`);
    });

    test('should handle meal plan errors', async () => {
      const error = { response: { status: 400 }, message: 'Request failed' };
      mockApiRequest.mockRejectedValue(error);
      const { result } = renderHook(() => useRecipes());

      let success = true;
      await act(async () => {
        success = await result.current.addRecipeToMealPlan(mockRecipe.id, '2024-01-15', 'dinner');
      });

      expect(success).toBe(false);
      expect(result.current.error).toBe('Invalid meal plan data or slot already occupied.');
    });
  });

  describe('Utility Functions', () => {
    test('should clear error', () => {
      const { result } = renderHook(() => useRecipes());

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBe(null);
    });
  });

  describe('Loading States', () => {
    test('should set loading state during fetch', async () => {
      let resolveApiRequest: (value: any) => void;
      const apiPromise = new Promise(resolve => {
        resolveApiRequest = resolve;
      });
      mockApiRequest.mockReturnValue(apiPromise);

      const { result } = renderHook(() => useRecipes());

      act(() => {
        result.current.fetchSavedRecipes();
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolveApiRequest([mockRecipe]);
        await apiPromise;
      });

      expect(result.current.loading).toBe(false);
    });
  });
});