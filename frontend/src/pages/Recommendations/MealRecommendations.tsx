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
  Rating,
  Checkbox,
  FormControlLabel,
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
  Star,
  CalendarToday,
  BookmarkAdd,
} from '@mui/icons-material';
import { MealRecommendation } from '../../types';
import { useRecommendationsCache } from '../../hooks/useRecommendationsCache';
import { useRecipes } from '../../hooks/useRecipes';

const MealRecommendations: React.FC = () => {
  const {
    recommendations,
    loading,
    error,
    availableProviders,
    selectedProvider,
    setSelectedProvider,
    refreshRecommendations,
    handleMealTypeFilter,
    clearError
  } = useRecommendationsCache();

  const {
    saveRecommendationAsRecipe,
    addRecommendationToMealPlan,
    rateRecipe,
    error: recipeError,
    clearError: clearRecipeError
  } = useRecipes();

  const [selectedMeal, setSelectedMeal] = useState<MealRecommendation | null>(null);
  const [ratingDialogOpen, setRatingDialogOpen] = useState(false);
  const [mealPlanDialogOpen, setMealPlanDialogOpen] = useState(false);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [wouldMakeAgain, setWouldMakeAgain] = useState(true);
  const [cookingNotes, setCookingNotes] = useState('');
  const [mealDate, setMealDate] = useState('');
  const [mealType, setMealType] = useState('dinner');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  const handleSaveRecipe = async (meal: MealRecommendation) => {
    const saved = await saveRecommendationAsRecipe(meal);
    if (saved) {
      setSnackbarMessage(`"${meal.name}" saved to your recipes!`);
      setSnackbarOpen(true);
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

  const handleOpenRatingDialog = (meal: MealRecommendation) => {
    setSelectedMeal(meal);
    // Reset form
    setRating(5);
    setReviewText('');
    setWouldMakeAgain(true);
    setCookingNotes('');
    setRatingDialogOpen(true);
  };

  const handleRateRecipe = async () => {
    if (!selectedMeal) return;

    // First save the recipe if not already saved
    const savedRecipe = await saveRecommendationAsRecipe(selectedMeal);
    if (!savedRecipe) return;

    const success = await rateRecipe({
      recipe_id: savedRecipe.id,
      rating,
      review_text: reviewText || undefined,
      would_make_again: wouldMakeAgain,
      cooking_notes: cookingNotes || undefined
    });

    if (success) {
      setSnackbarMessage(`Rating submitted for "${selectedMeal.name}"!`);
      setSnackbarOpen(true);
      setRatingDialogOpen(false);
    }
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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Meal Recommendations
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
          startIcon={<Refresh />}
          onClick={() => refreshRecommendations()}
          disabled={loading}
        >
          Get New Ideas
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

      {/* Meal Type Filters */}
      <Box mb={3}>
        <Typography variant="h6" gutterBottom>
          Filter by Meal Type
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Button variant="outlined" onClick={() => refreshRecommendations()}>
            All Meals
          </Button>
          <Button variant="outlined" onClick={() => handleMealTypeFilter('breakfast')}>
            Breakfast
          </Button>
          <Button variant="outlined" onClick={() => handleMealTypeFilter('lunch')}>
            Lunch
          </Button>
          <Button variant="outlined" onClick={() => handleMealTypeFilter('dinner')}>
            Dinner
          </Button>
          <Button variant="outlined" onClick={() => handleMealTypeFilter('snack')}>
            Snacks
          </Button>
        </Box>
      </Box>

      {loading ? (
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
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, 
            gap: 3 
          }}
        >
          {recommendations.map((meal, index) => (
            <Card key={index} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Box>
                      <Typography variant="h6" component="h2" gutterBottom>
                        {meal.name}
                      </Typography>
                      {meal.ai_generated && (
                        <Box display="flex" gap={1} flexWrap="wrap">
                          <Chip
                            icon={<AutoAwesome />}
                            label="AI Generated"
                            color="primary"
                            size="small"
                          />
                          {meal.ai_provider && (
                            <Chip
                              label={meal.ai_provider === 'claude' ? 'Claude AI' : 
                                     meal.ai_provider === 'groq' ? 'Groq' : 
                                     meal.ai_provider === 'perplexity' ? 'Perplexity' :
                                     meal.ai_provider.charAt(0).toUpperCase() + meal.ai_provider.slice(1)}
                              color="secondary"
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      )}
                    </Box>
                    <Chip
                      label={`${meal.pantry_usage_score}%`}
                      color={getPantryScoreColor(meal.pantry_usage_score) as any}
                      size="small"
                      title="Pantry Usage Score"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {meal.description}
                  </Typography>

                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      icon={<Timer />}
                      label={`${meal.prep_time} min`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={meal.difficulty}
                      size="small"
                      color={getDifficultyColor(meal.difficulty) as any}
                    />
                    <Chip
                      icon={<People />}
                      label={`${meal.servings} servings`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>

                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Tags:
                    </Typography>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {meal.tags.map((tag, tagIndex) => (
                        <Chip key={tagIndex} label={tag} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>

                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Ingredients needed:
                    </Typography>
                    <Box>
                      {meal.ingredients_needed.slice(0, 3).map((ingredient, ingredientIndex) => (
                        <Box key={ingredientIndex} display="flex" alignItems="center" gap={1}>
                          {ingredient.have_in_pantry ? 
                            <CheckCircle color="success" sx={{ fontSize: 16 }} /> : 
                            <RadioButtonUnchecked color="disabled" sx={{ fontSize: 16 }} />
                          }
                          <Typography variant="caption">
                            {ingredient.name} ({ingredient.quantity} {ingredient.unit})
                          </Typography>
                        </Box>
                      ))}
                      {meal.ingredients_needed.length > 3 && (
                        <Typography variant="caption" color="text.secondary">
                          +{meal.ingredients_needed.length - 3} more ingredients
                        </Typography>
                      )}
                    </Box>
                  </Box>

                  <Typography variant="body2" color="primary" sx={{ fontStyle: 'italic' }}>
                    {meal.nutrition_notes}
                  </Typography>
                </CardContent>

                <Box p={2} pt={0}>
                  <Box display="flex" gap={1} mb={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Save />}
                      onClick={() => handleSaveRecipe(meal)}
                      sx={{ flex: 1 }}
                    >
                      Save
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Star />}
                      onClick={() => handleOpenRatingDialog(meal)}
                      sx={{ flex: 1 }}
                    >
                      Rate
                    </Button>
                  </Box>
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<CalendarToday />}
                      onClick={() => handleOpenMealPlanDialog(meal)}
                      sx={{ flex: 1 }}
                    >
                      Add to Plan
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<Restaurant />}
                      onClick={() => setSelectedMeal(meal)}
                      sx={{ flex: 1 }}
                    >
                      View Recipe
                    </Button>
                  </Box>
                </Box>
              </Card>
          ))}
        </Box>
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
                  <Typography variant="h6">Instructions ({selectedMeal.instructions.length} steps)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {selectedMeal.instructions.map((instruction, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={`Step ${index + 1}`}
                          secondary={instruction}
                        />
                      </ListItem>
                    ))}
                  </List>
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

      {/* Rating Dialog */}
      <Dialog open={ratingDialogOpen} onClose={() => setRatingDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rate Recipe: {selectedMeal?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography component="legend">Overall Rating</Typography>
            <Rating
              name="recipe-rating"
              value={rating}
              onChange={(_, newValue) => setRating(newValue || 5)}
              size="large"
            />
          </Box>
          
          <TextField
            autoFocus
            margin="dense"
            label="Review (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            placeholder="How was this recipe? Any tips or modifications?"
            sx={{ mt: 2 }}
          />
          
          <FormControlLabel
            control={
              <Checkbox
                checked={wouldMakeAgain}
                onChange={(e) => setWouldMakeAgain(e.target.checked)}
              />
            }
            label="Would make this recipe again"
            sx={{ mt: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Cooking Notes (optional)"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={cookingNotes}
            onChange={(e) => setCookingNotes(e.target.value)}
            placeholder="Any notes about preparation, substitutions, etc."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRatingDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRateRecipe} variant="contained">
            Submit Rating
          </Button>
        </DialogActions>
      </Dialog>

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