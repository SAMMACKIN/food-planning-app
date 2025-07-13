import { useState, useEffect, useCallback } from 'react';
import { apiRequest } from '../services/api';
import { Recipe, RecipeCreate, MealRecommendation, RecipeRating, RecipeRatingCreate } from '../types';
import { useAuthStore } from '../store/authStore';

export const useRecipes = () => {
  const { isAuthenticated } = useAuthStore();
  const [savedRecipes, setSavedRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSavedRecipes = useCallback(async (search?: string, difficulty?: string, tags?: string) => {
    console.log('📚 fetchSavedRecipes called - starting fetch...');
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (difficulty) params.append('difficulty', difficulty);
      if (tags) params.append('tags', tags);
      
      const endpoint = `/recipes${params.toString() ? `?${params.toString()}` : ''}`;
      const recipes = await apiRequest<Recipe[]>('GET', endpoint);
      setSavedRecipes(recipes);
    } catch (error: any) {
      console.error('Error fetching saved recipes:', error);
      setError('Failed to fetch saved recipes');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveRecipe = useCallback(async (recipeData: RecipeCreate): Promise<Recipe | null> => {
    try {
      setError(null);
      console.log('🍽️ Saving recipe:', recipeData.name);
      console.log('📋 Recipe data:', recipeData);
      
      // Check authentication before attempting save
      const token = localStorage.getItem('access_token');
      if (!token) {
        const errorMsg = 'No authentication token found. Please log in again.';
        console.error('❌', errorMsg);
        setError(errorMsg);
        return null;
      }
      
      console.log('🔑 Token exists, length:', token.length);
      
      const savedRecipe = await apiRequest<Recipe>('POST', '/recipes', recipeData);
      console.log('✅ Recipe saved successfully:', savedRecipe);
      
      // Add to local state
      setSavedRecipes(prev => [savedRecipe, ...prev]);
      
      return savedRecipe;
    } catch (error: any) {
      console.error('❌ Error saving recipe:', error);
      console.error('❌ Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers
        }
      });
      
      let errorMessage = 'Failed to save recipe';
      if (error.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.response?.status === 422) {
        errorMessage = 'Invalid recipe data. Please check all fields.';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if the backend is running.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      return null;
    }
  }, []);

  const saveRecommendationAsRecipe = useCallback(async (recommendation: MealRecommendation): Promise<Recipe | null> => {
    // Check if we already have this recipe saved to avoid duplicates
    const existingRecipe = savedRecipes.find(recipe => 
      recipe.name === recommendation.name && 
      recipe.source === 'recommendation' &&
      recipe.ai_generated === recommendation.ai_generated
    );
    
    if (existingRecipe) {
      console.log('🔄 Recipe already saved, returning existing:', existingRecipe.name);
      return existingRecipe;
    }

    const recipeData: RecipeCreate = {
      name: recommendation.name,
      description: recommendation.description,
      prep_time: recommendation.prep_time,
      difficulty: recommendation.difficulty,
      servings: recommendation.servings,
      ingredients_needed: recommendation.ingredients_needed,
      instructions: recommendation.instructions,
      tags: recommendation.tags,
      nutrition_notes: recommendation.nutrition_notes,
      pantry_usage_score: recommendation.pantry_usage_score,
      ai_generated: recommendation.ai_generated,
      ai_provider: recommendation.ai_provider,
      source: 'recommendation'
    };

    return await saveRecipe(recipeData);
  }, [saveRecipe, savedRecipes]);

  const deleteRecipe = useCallback(async (recipeId: string): Promise<boolean> => {
    try {
      setError(null);
      await apiRequest('DELETE', `/recipes/${recipeId}`);
      
      // Remove from local state
      setSavedRecipes(prev => prev.filter(recipe => recipe.id !== recipeId));
      
      return true;
    } catch (error: any) {
      console.error('Error deleting recipe:', error);
      setError('Failed to delete recipe');
      return false;
    }
  }, []);

  // Recipe Rating Functions
  const createRecipeRating = useCallback(async (
    recipeId: string, 
    ratingData: RecipeRatingCreate
  ): Promise<RecipeRating | null> => {
    try {
      setError(null);
      console.log('⭐ Creating recipe rating:', { recipeId, ratingData });
      
      const rating = await apiRequest<RecipeRating>('POST', `/recipes/${recipeId}/ratings`, ratingData);
      console.log('✅ Rating created successfully:', rating);
      
      return rating;
    } catch (error: any) {
      console.error('❌ Error creating recipe rating:', error);
      
      let errorMessage = 'Failed to save rating';
      if (error.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Recipe not found. It may have been deleted.';
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid rating data. Please check all fields.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      return null;
    }
  }, []);

  const getRecipeRatings = useCallback(async (recipeId: string): Promise<RecipeRating[]> => {
    try {
      setError(null);
      const ratings = await apiRequest<RecipeRating[]>('GET', `/recipes/${recipeId}/ratings`);
      return ratings;
    } catch (error: any) {
      console.error('❌ Error fetching recipe ratings:', error);
      setError('Failed to load ratings');
      return [];
    }
  }, []);

  const updateRecipeRating = useCallback(async (
    recipeId: string, 
    ratingId: string, 
    ratingData: RecipeRatingCreate
  ): Promise<RecipeRating | null> => {
    try {
      setError(null);
      console.log('⭐ Updating recipe rating:', { recipeId, ratingId, ratingData });
      
      const rating = await apiRequest<RecipeRating>('PUT', `/recipes/${recipeId}/ratings/${ratingId}`, ratingData);
      console.log('✅ Rating updated successfully:', rating);
      
      return rating;
    } catch (error: any) {
      console.error('❌ Error updating recipe rating:', error);
      
      let errorMessage = 'Failed to update rating';
      if (error.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Rating not found. It may have been deleted.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      return null;
    }
  }, []);

  const deleteRecipeRating = useCallback(async (recipeId: string, ratingId: string): Promise<boolean> => {
    try {
      setError(null);
      await apiRequest('DELETE', `/recipes/${recipeId}/ratings/${ratingId}`);
      console.log('✅ Rating deleted successfully');
      return true;
    } catch (error: any) {
      console.error('❌ Error deleting recipe rating:', error);
      setError('Failed to delete rating');
      return false;
    }
  }, []);

  const addRecipeToMealPlan = useCallback(async (
    recipeId: string, 
    mealDate: string, 
    mealType: string
  ): Promise<boolean> => {
    try {
      setError(null);
      console.log('📅 Adding recipe to meal plan:', {recipeId, mealDate, mealType});
      
      // Check authentication before attempting
      const token = localStorage.getItem('access_token');
      if (!token) {
        const errorMsg = 'No authentication token found. Please log in again.';
        console.error('❌', errorMsg);
        setError(errorMsg);
        return false;
      }
      
      await apiRequest('POST', `/recipes/${recipeId}/add-to-meal-plan?meal_date=${mealDate}&meal_type=${mealType}`);
      console.log('✅ Recipe added to meal plan successfully');
      return true;
    } catch (error: any) {
      console.error('❌ Error adding recipe to meal plan:', error);
      console.error('❌ Meal plan error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        recipeId,
        mealDate,
        mealType
      });
      
      let errorMessage = 'Failed to add recipe to meal plan';
      if (error.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Recipe not found. It may have been deleted.';
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid meal plan data or slot already occupied.';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if the backend is running.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      return false;
    }
  }, []);

  const addRecommendationToMealPlan = useCallback(async (
    recommendation: MealRecommendation,
    mealDate: string,
    mealType: string
  ): Promise<boolean> => {
    // First save the recipe, then add to meal plan
    const savedRecipe = await saveRecommendationAsRecipe(recommendation);
    if (!savedRecipe) {
      return false;
    }
    
    return await addRecipeToMealPlan(savedRecipe.id, mealDate, mealType);
  }, [saveRecommendationAsRecipe, addRecipeToMealPlan]);

  // Auto-fetch recipes when user becomes authenticated
  useEffect(() => {
    if (isAuthenticated && savedRecipes.length === 0) {
      fetchSavedRecipes();
    }
  }, [isAuthenticated, savedRecipes.length, fetchSavedRecipes]);

  return {
    savedRecipes,
    loading,
    error,
    fetchSavedRecipes,
    saveRecipe,
    saveRecommendationAsRecipe,
    deleteRecipe,
    // Rating functions
    createRecipeRating,
    getRecipeRatings,
    updateRecipeRating,
    deleteRecipeRating,
    // Meal plan functions
    addRecipeToMealPlan,
    addRecommendationToMealPlan,
    clearError: () => setError(null)
  };
};