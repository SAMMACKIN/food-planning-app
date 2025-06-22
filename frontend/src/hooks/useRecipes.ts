import { useState, useEffect, useCallback } from 'react';
import { apiRequest } from '../services/api';
import { SavedRecipe, SavedRecipeCreate, RecipeRating, RecipeRatingCreate, MealRecommendation } from '../types';

export const useRecipes = () => {
  const [savedRecipes, setSavedRecipes] = useState<SavedRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSavedRecipes = useCallback(async (search?: string, difficulty?: string, tags?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (difficulty) params.append('difficulty', difficulty);
      if (tags) params.append('tags', tags);
      
      const endpoint = `/recipes${params.toString() ? `?${params.toString()}` : ''}`;
      const recipes = await apiRequest<SavedRecipe[]>('GET', endpoint);
      setSavedRecipes(recipes);
    } catch (error: any) {
      console.error('Error fetching saved recipes:', error);
      setError('Failed to fetch saved recipes');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveRecipe = useCallback(async (recipeData: SavedRecipeCreate): Promise<SavedRecipe | null> => {
    try {
      setError(null);
      const savedRecipe = await apiRequest<SavedRecipe>('POST', '/recipes', recipeData);
      
      // Add to local state
      setSavedRecipes(prev => [savedRecipe, ...prev]);
      
      return savedRecipe;
    } catch (error: any) {
      console.error('Error saving recipe:', error);
      setError('Failed to save recipe');
      return null;
    }
  }, []);

  const saveRecommendationAsRecipe = useCallback(async (recommendation: MealRecommendation): Promise<SavedRecipe | null> => {
    const recipeData: SavedRecipeCreate = {
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
  }, [saveRecipe]);

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

  const rateRecipe = useCallback(async (ratingData: RecipeRatingCreate): Promise<RecipeRating | null> => {
    try {
      setError(null);
      const rating = await apiRequest<RecipeRating>('POST', `/recipes/${ratingData.recipe_id}/ratings`, ratingData);
      
      // Update local recipe state with new average rating (approximation)
      setSavedRecipes(prev => prev.map(recipe => {
        if (recipe.id === ratingData.recipe_id) {
          return {
            ...recipe,
            times_cooked: recipe.times_cooked + 1,
            last_cooked: new Date().toISOString()
          };
        }
        return recipe;
      }));
      
      return rating;
    } catch (error: any) {
      console.error('Error rating recipe:', error);
      setError('Failed to rate recipe');
      return null;
    }
  }, []);

  const addRecipeToMealPlan = useCallback(async (
    recipeId: string, 
    mealDate: string, 
    mealType: string
  ): Promise<boolean> => {
    try {
      setError(null);
      await apiRequest('POST', `/recipes/${recipeId}/add-to-meal-plan?meal_date=${mealDate}&meal_type=${mealType}`);
      return true;
    } catch (error: any) {
      console.error('Error adding recipe to meal plan:', error);
      setError(error.response?.data?.detail || 'Failed to add recipe to meal plan');
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

  // Auto-fetch recipes on mount
  useEffect(() => {
    fetchSavedRecipes();
  }, [fetchSavedRecipes]);

  return {
    savedRecipes,
    loading,
    error,
    fetchSavedRecipes,
    saveRecipe,
    saveRecommendationAsRecipe,
    deleteRecipe,
    rateRecipe,
    addRecipeToMealPlan,
    addRecommendationToMealPlan,
    clearError: () => setError(null)
  };
};