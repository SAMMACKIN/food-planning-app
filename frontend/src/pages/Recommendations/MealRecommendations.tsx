import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Snackbar,
} from '@mui/material';
import {
  Restaurant,
  Timer,
  People,
  CheckCircle,
  RadioButtonUnchecked,
  ExpandMore,
  Refresh,
  AutoAwesome,
  Settings,
  Save,
  CalendarToday,
  Psychology,
  SmartToy,
  AutoFixHigh,
  Star,
  CloudDownload,
} from '@mui/icons-material';
import { MealRecommendation, Recipe, RecipeRating } from '../../types';
import { useRecommendationsCache } from '../../hooks/useRecommendationsCache';
import { useRecipes } from '../../hooks/useRecipes';
import RecipeInstructions from '../../components/Recipe/RecipeInstructions';
import RecipeDebugPanel from '../../components/Recipe/RecipeDebugPanel';
import RateRecipeDialog from '../../components/Recipe/RateRecipeDialog';

const MealRecommendations: React.FC = () => {
  const {
    recommendations,
    loading,
    backgroundLoading,
    backgroundLoadCompleted,
    error,
    availableProviders,
    selectedProvider,
    setSelectedProvider,
    refreshRecommendations,
    refreshRecommendationsInBackground,
    handleMealTypeFilter,
    clearError,
    clearBackgroundLoadCompleted,
    resetState
  } = useRecommendationsCache();

  const {
    saveRecommendationAsRecipe,
    addRecommendationToMealPlan,
    createRecipeRating,
    error: recipeError,
    clearError: clearRecipeError
  } = useRecipes();

  const [selectedMeal, setSelectedMeal] = useState<MealRecommendation | null>(null);
  const [mealPlanDialogOpen, setMealPlanDialogOpen] = useState(false);
  const [mealDate, setMealDate] = useState('');
  const [mealType, setMealType] = useState('dinner');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [filteredRecommendations, setFilteredRecommendations] = useState<MealRecommendation[]>([]);
  const [activeFilters, setActiveFilters] = useState({
    difficulty: 'all',
    prepTime: 'all'
  });
  // Rating dialog state
  const [ratingDialogOpen, setRatingDialogOpen] = useState(false);
  const [recipeToRate, setRecipeToRate] = useState<Recipe | null>(null);

  const handleSaveRecipe = async (meal: MealRecommendation) => {
    console.log('🍽️ Attempting to save recipe:', meal.name);
    const saved = await saveRecommendationAsRecipe(meal);
    if (saved) {
      setSnackbarMessage(`"${meal.name}" saved to your recipes!`);
      setSnackbarOpen(true);
      console.log('✅ Recipe save successful:', saved.id);
    } else {
      console.error('❌ Recipe save failed');
      // The error will be shown via the error state from useRecipes hook
    }
  };

  const handleOpenMealPlanDialog = (meal: MealRecommendation) => {
    setSelectedMeal(meal);
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    setMealDate(today);
    setMealPlanDialogOpen(true);
  };

  const handleAddToMealPlan = async () => {
    if (!selectedMeal || !mealDate || !mealType) return;

    const success = await addRecommendationToMealPlan(selectedMeal, mealDate, mealType);
    if (success) {
      setSnackbarMessage(`"${selectedMeal.name}" added to ${mealType} on ${mealDate}!`);
      setSnackbarOpen(true);
      setMealPlanDialogOpen(false);
    }
  };

  const handleOpenRatingDialog = async (meal: MealRecommendation) => {
    // First save the recipe if it hasn't been saved yet
    const savedRecipe = await saveRecommendationAsRecipe(meal);
    if (savedRecipe) {
      setRecipeToRate(savedRecipe);
      setRatingDialogOpen(true);
    }
  };

  const handleSubmitRating = async (ratingData: Omit<RecipeRating, 'id' | 'recipe_id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<boolean> => {
    if (!recipeToRate) return false;
    
    const rating = await createRecipeRating(recipeToRate.id, ratingData);
    if (rating) {
      setSnackbarMessage(`Rating saved for "${recipeToRate.name}"!`);
      setSnackbarOpen(true);
      return true;
    }
    return false;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'error';
      default: return 'default';
    }
  };

  const getPantryScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getAIProviderInfo = (provider?: string) => {
    switch (provider?.toLowerCase()) {
      case 'claude':
        return { name: 'Claude AI', icon: Psychology, color: '#FF6B35' };
      case 'perplexity':
        return { name: 'Perplexity', icon: AutoFixHigh, color: '#1FB6FF' };
      case 'groq':
        return { name: 'Groq', icon: SmartToy, color: '#F7931E' };
      default:
        return { name: 'AI Generated', icon: AutoAwesome, color: '#9C27B0' };
    }
  };

  const handleDifficultyFilter = (difficulty: string) => {
    setActiveFilters(prev => ({ ...prev, difficulty }));
  };

  const handleTimeFilter = (prepTime: string) => {
    setActiveFilters(prev => ({ ...prev, prepTime }));
  };

  // Cleanup: reset loading state when component unmounts to prevent navigation blocking
  useEffect(() => {
    return () => {
      resetState();
    };
  }, [resetState]);

  // Apply filters whenever recommendations or filters change
  React.useEffect(() => {
    let filtered = [...recommendations];

    // Apply difficulty filter
    if (activeFilters.difficulty !== 'all') {
      filtered = filtered.filter(meal => 
        meal.difficulty.toLowerCase() === activeFilters.difficulty.toLowerCase()
      );
    }

    // Apply prep time filter
    if (activeFilters.prepTime !== 'all') {
      filtered = filtered.filter(meal => {
        const prepTime = meal.prep_time;
        switch (activeFilters.prepTime) {
          case 'quick':
            return prepTime <= 30;
          case 'medium':
            return prepTime > 30 && prepTime <= 60;
          case 'long':
            return prepTime > 60;
          default:
            return true;
        }
      });
    }

    setFilteredRecommendations(filtered);
  }, [recommendations, activeFilters]);

  // Show notification when background loading completes
  React.useEffect(() => {
    if (backgroundLoadCompleted) {
      setSnackbarMessage(`🎉 Fresh recommendations loaded! Found ${recommendations.length} new meal ideas.`);
      setSnackbarOpen(true);
      clearBackgroundLoadCompleted();
    }
  }, [backgroundLoadCompleted, recommendations.length, clearBackgroundLoadCompleted]);


  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesome color="primary" />
            Meal Recommendations
            {backgroundLoading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="caption" color="text.secondary">
                  Getting fresh ideas...
                </Typography>
              </Box>
            )}
          </Typography>
          {availableProviders.length === 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AutoAwesome sx={{ mr: 1 }} />
              No AI providers available. Please configure Claude or Groq API keys.
            </Alert>
          )}
        </Box>
        <Button
          variant="contained"
          startIcon={backgroundLoading ? <CloudDownload /> : <Refresh />}
          onClick={() => {
            // Use background loading if we already have recommendations
            if (recommendations.length > 0) {
              refreshRecommendationsInBackground();
            } else {
              refreshRecommendations();
            }
          }}
          disabled={loading || backgroundLoading}
        >
          {backgroundLoading ? 'Loading...' : 'Get New Ideas'}
        </Button>
      </Box>

      {(error || recipeError) && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          onClose={() => {
            clearError();
            clearRecipeError();
          }}
        >
          {error || recipeError}
        </Alert>
      )}

      {/* Debug Panel - only show when there are recipe errors */}
      {recipeError && (
        <RecipeDebugPanel 
          error={recipeError} 
          onClearError={clearRecipeError}
        />
      )}

      {/* AI Provider Selection */}
      {availableProviders.length > 1 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Settings color="primary" />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6">
                  AI Model Selection
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose which AI model to generate your meal recommendations
                </Typography>
              </Box>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>AI Provider</InputLabel>
                <Select
                  value={selectedProvider}
                  label="AI Provider"
                  onChange={(e) => setSelectedProvider(e.target.value)}
                >
                  {availableProviders.map((provider) => (
                    <MenuItem key={provider} value={provider}>
                      {provider === 'claude' ? 'Claude AI' : 
                       provider === 'groq' ? 'Groq (Llama)' : 
                       provider === 'perplexity' ? 'Perplexity AI' :
                       provider.charAt(0).toUpperCase() + provider.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          🔍 Filter Recipes
        </Typography>
        
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            Meal Type
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            <Button 
              size="small" 
              variant="outlined" 
              onClick={() => {
                if (recommendations.length > 0) {
                  refreshRecommendationsInBackground();
                } else {
                  refreshRecommendations();
                }
              }}
              disabled={loading || backgroundLoading}
            >
              All Meals
            </Button>
            <Button 
              size="small" 
              variant="outlined" 
              onClick={() => handleMealTypeFilter('breakfast')}
              disabled={loading || backgroundLoading}
            >
              Breakfast
            </Button>
            <Button 
              size="small" 
              variant="outlined" 
              onClick={() => handleMealTypeFilter('lunch')}
              disabled={loading || backgroundLoading}
            >
              Lunch
            </Button>
            <Button 
              size="small" 
              variant="outlined" 
              onClick={() => handleMealTypeFilter('dinner')}
              disabled={loading || backgroundLoading}
            >
              Dinner
            </Button>
            <Button 
              size="small" 
              variant="outlined" 
              onClick={() => handleMealTypeFilter('snack')}
              disabled={loading || backgroundLoading}
            >
              Snacks
            </Button>
          </Box>
        </Box>

        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            Difficulty
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            <Button 
              size="small" 
              variant={activeFilters.difficulty === 'all' ? 'contained' : 'outlined'} 
              onClick={() => handleDifficultyFilter('all')}
            >
              All Levels
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.difficulty === 'Easy' ? 'contained' : 'outlined'} 
              color="success" 
              onClick={() => handleDifficultyFilter('Easy')}
            >
              Easy
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.difficulty === 'Medium' ? 'contained' : 'outlined'} 
              color="warning" 
              onClick={() => handleDifficultyFilter('Medium')}
            >
              Medium
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.difficulty === 'Hard' ? 'contained' : 'outlined'} 
              color="error" 
              onClick={() => handleDifficultyFilter('Hard')}
            >
              Hard
            </Button>
          </Box>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Preparation Time
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            <Button 
              size="small" 
              variant={activeFilters.prepTime === 'all' ? 'contained' : 'outlined'} 
              onClick={() => handleTimeFilter('all')}
            >
              Any Time
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.prepTime === 'quick' ? 'contained' : 'outlined'} 
              onClick={() => handleTimeFilter('quick')}
            >
              {'≤'} 30 min
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.prepTime === 'medium' ? 'contained' : 'outlined'} 
              onClick={() => handleTimeFilter('medium')}
            >
              30-60 min
            </Button>
            <Button 
              size="small" 
              variant={activeFilters.prepTime === 'long' ? 'contained' : 'outlined'} 
              onClick={() => handleTimeFilter('long')}
            >
              {'>'} 60 min
            </Button>
          </Box>
        </Box>
      </Card>

      {loading && recommendations.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            {availableProviders.length > 0 ? `${selectedProvider.charAt(0).toUpperCase() + selectedProvider.slice(1)} AI is crafting personalized recommendations...` : 'Loading recommendations...'}
          </Typography>
        </Box>
      ) : (
        <Box 
          sx={{ 
            display: 'grid', 
            gridTemplateColumns: { 
              xs: '1fr', 
              sm: 'repeat(2, 1fr)', 
              md: 'repeat(3, 1fr)', 
              lg: 'repeat(4, 1fr)' 
            }, 
            gap: 2,
            mb: 4
          }}
        >
          {filteredRecommendations.map((meal, index) => (
            <Card key={index} sx={{ height: '100%', display: 'flex', flexDirection: 'column', maxHeight: 320 }}>
              <CardContent sx={{ flexGrow: 1, p: 2, '&:last-child': { pb: 1 } }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600, fontSize: '0.95rem', lineHeight: 1.2 }}>
                    {meal.name}
                  </Typography>
                  <Chip
                    label={`${meal.pantry_usage_score}%`}
                    color={getPantryScoreColor(meal.pantry_usage_score) as any}
                    size="small"
                    sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ 
                  fontSize: '0.8rem',
                  lineHeight: 1.3,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  mb: 1.5
                }}>
                  {meal.description}
                </Typography>

                <Box display="flex" gap={0.5} mb={1.5} flexWrap="wrap">
                  <Chip
                    icon={<Timer />}
                    label={`${meal.prep_time}m`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 22 }}
                  />
                  <Chip
                    label={meal.difficulty}
                    size="small"
                    color={getDifficultyColor(meal.difficulty) as any}
                    sx={{ fontSize: '0.7rem', height: 22 }}
                  />
                  <Chip
                    icon={<People />}
                    label={`${meal.servings}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 22 }}
                  />
                  {meal.ai_provider && (
                    <Chip
                      icon={React.createElement(getAIProviderInfo(meal.ai_provider).icon)}
                      label={getAIProviderInfo(meal.ai_provider).name}
                      size="small"
                      sx={{ 
                        fontSize: '0.7rem', 
                        height: 22,
                        backgroundColor: getAIProviderInfo(meal.ai_provider).color + '20',
                        color: getAIProviderInfo(meal.ai_provider).color,
                        '& .MuiChip-icon': {
                          color: getAIProviderInfo(meal.ai_provider).color
                        }
                      }}
                    />
                  )}
                </Box>

                <Box mb={1.5}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', mb: 0.5, display: 'block' }}>
                    Need to buy:
                  </Typography>
                  <Box>
                    {meal.ingredients_needed.filter(ing => !ing.have_in_pantry).slice(0, 3).map((ingredient, ingredientIndex) => (
                      <Typography key={ingredientIndex} variant="caption" sx={{ 
                        fontSize: '0.75rem', 
                        display: 'block',
                        color: 'text.secondary'
                      }}>
                        • {ingredient.name}
                      </Typography>
                    ))}
                    {meal.ingredients_needed.filter(ing => !ing.have_in_pantry).length > 3 && (
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        +{meal.ingredients_needed.filter(ing => !ing.have_in_pantry).length - 3} more
                      </Typography>
                    )}
                  </Box>
                </Box>
                </CardContent>

                <Box sx={{ p: 1.5, pt: 0 }}>
                  <Box display="flex" gap={0.5} mb={0.5}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Save />}
                      onClick={() => handleSaveRecipe(meal)}
                      sx={{ flex: 1, fontSize: '0.7rem', py: 0.5 }}
                    >
                      Save
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Star />}
                      onClick={() => handleOpenRatingDialog(meal)}
                      sx={{ flex: 1, fontSize: '0.7rem', py: 0.5 }}
                    >
                      Rate
                    </Button>
                  </Box>
                  <Box display="flex" gap={0.5}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<CalendarToday />}
                      onClick={() => handleOpenMealPlanDialog(meal)}
                      sx={{ flex: 1, fontSize: '0.7rem', py: 0.5 }}
                    >
                      Plan
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<Restaurant />}
                      onClick={() => setSelectedMeal(meal)}
                      sx={{ flex: 1, fontSize: '0.7rem', py: 0.5 }}
                    >
                      View
                    </Button>
                  </Box>
                </Box>
              </Card>
          ))}
        </Box>
      )}

      {filteredRecommendations.length === 0 && recommendations.length > 0 && !loading && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Restaurant sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No recipes match your filters
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Try adjusting your difficulty or time filters to see more options
            </Typography>
            <Button variant="outlined" onClick={() => setActiveFilters({ difficulty: 'all', prepTime: 'all' })}>
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      )}

      {recommendations.length === 0 && !loading && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Restaurant sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No recommendations yet
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Add some ingredients to your pantry and family members to get personalized meal suggestions
            </Typography>
            <Button variant="contained" onClick={() => refreshRecommendations()}>
              Get Recommendations
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Recipe Detail Dialog */}
      <Dialog 
        open={!!selectedMeal} 
        onClose={() => setSelectedMeal(null)} 
        maxWidth="md" 
        fullWidth
      >
        {selectedMeal && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                {selectedMeal.name}
                <Box display="flex" gap={1}>
                  <Chip
                    icon={<Timer />}
                    label={`${selectedMeal.prep_time} min`}
                    size="small"
                  />
                  <Chip
                    label={selectedMeal.difficulty}
                    size="small"
                    color={getDifficultyColor(selectedMeal.difficulty) as any}
                  />
                  {selectedMeal.ai_provider && (
                    <Chip
                      icon={React.createElement(getAIProviderInfo(selectedMeal.ai_provider).icon)}
                      label={getAIProviderInfo(selectedMeal.ai_provider).name}
                      size="small"
                      sx={{ 
                        backgroundColor: getAIProviderInfo(selectedMeal.ai_provider).color + '20',
                        color: getAIProviderInfo(selectedMeal.ai_provider).color,
                        '& .MuiChip-icon': {
                          color: getAIProviderInfo(selectedMeal.ai_provider).color
                        }
                      }}
                    />
                  )}
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedMeal.description}
              </Typography>

              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">Ingredients ({selectedMeal.ingredients_needed.length})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {selectedMeal.ingredients_needed.map((ingredient, index) => (
                      <ListItem key={index}>
                        <Box display="flex" alignItems="center" gap={1} width="100%">
                          {ingredient.have_in_pantry ? 
                            <CheckCircle color="success" sx={{ fontSize: 20 }} /> : 
                            <RadioButtonUnchecked color="disabled" sx={{ fontSize: 20 }} />
                          }
                          <ListItemText 
                            primary={`${ingredient.quantity} ${ingredient.unit} ${ingredient.name}`}
                            secondary={ingredient.have_in_pantry ? 'Available in pantry' : 'Need to buy'}
                          />
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">Cooking Instructions ({selectedMeal.instructions.length} steps)</Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 0 }}>
                  <RecipeInstructions 
                    instructions={selectedMeal.instructions} 
                    prepTime={selectedMeal.prep_time}
                  />
                </AccordionDetails>
              </Accordion>

              <Divider sx={{ my: 2 }} />

              <Box>
                <Typography variant="h6" gutterBottom>Nutrition Notes</Typography>
                <Typography variant="body2" color="primary" sx={{ fontStyle: 'italic' }}>
                  {selectedMeal.nutrition_notes}
                </Typography>
              </Box>

              <Box mt={2}>
                <Typography variant="h6" gutterBottom>Recipe Tags</Typography>
                <Box display="flex" gap={0.5} flexWrap="wrap">
                  {selectedMeal.tags.map((tag, index) => (
                    <Chip key={index} label={tag} size="small" />
                  ))}
                </Box>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedMeal(null)}>Close</Button>
              <Button 
                startIcon={<Save />} 
                onClick={() => selectedMeal && handleSaveRecipe(selectedMeal)}
              >
                Save Recipe
              </Button>
              <Button 
                startIcon={<Star />} 
                onClick={() => selectedMeal && handleOpenRatingDialog(selectedMeal)}
              >
                Rate Recipe
              </Button>
              <Button 
                variant="contained" 
                startIcon={<CalendarToday />}
                onClick={() => selectedMeal && handleOpenMealPlanDialog(selectedMeal)}
              >
                Add to Meal Plan
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Rate Recipe Dialog */}
      <RateRecipeDialog
        open={ratingDialogOpen}
        onClose={() => {
          setRatingDialogOpen(false);
          setRecipeToRate(null);
        }}
        recipe={recipeToRate}
        onSubmit={handleSubmitRating}
      />

      {/* Meal Plan Dialog */}
      <Dialog open={mealPlanDialogOpen} onClose={() => setMealPlanDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add to Meal Plan: {selectedMeal?.name}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Date"
            type="date"
            fullWidth
            variant="outlined"
            value={mealDate}
            onChange={(e) => setMealDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ mt: 2 }}
          />
          
          <FormControl fullWidth margin="dense" sx={{ mt: 2 }}>
            <InputLabel>Meal Type</InputLabel>
            <Select
              value={mealType}
              label="Meal Type"
              onChange={(e) => setMealType(e.target.value)}
            >
              <MenuItem value="breakfast">Breakfast</MenuItem>
              <MenuItem value="lunch">Lunch</MenuItem>
              <MenuItem value="dinner">Dinner</MenuItem>
              <MenuItem value="snack">Snack</MenuItem>
            </Select>
          </FormControl>
          
          {selectedMeal && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Recipe Summary:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedMeal.description}
              </Typography>
              <Box display="flex" gap={1} mt={1}>
                <Chip size="small" icon={<Timer />} label={`${selectedMeal.prep_time} min`} />
                <Chip size="small" icon={<People />} label={`${selectedMeal.servings} servings`} />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMealPlanDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleAddToMealPlan} 
            variant="contained"
            disabled={!mealDate || !mealType}
          >
            Add to Plan
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />

    </Box>
  );
};

export default MealRecommendations;