import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
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
} from '@mui/icons-material';
import { MealRecommendation, MealRecommendationRequest } from '../../types';
import { apiRequest } from '../../services/api';

const MealRecommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<MealRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMeal, setSelectedMeal] = useState<MealRecommendation | null>(null);
  const [claudeAvailable, setClaudeAvailable] = useState<boolean>(false);

  const checkClaudeStatus = async () => {
    try {
      const status = await apiRequest<{ claude_available: boolean; message: string }>('GET', '/recommendations/status');
      setClaudeAvailable(status.claude_available);
    } catch (error) {
      console.error('Error checking Claude status:', error);
    }
  };

  const fetchRecommendations = async (request: MealRecommendationRequest = {}) => {
    try {
      setLoading(true);
      setError(null);
      const recs = await apiRequest<MealRecommendation[]>('POST', '/recommendations', request);
      setRecommendations(recs);
    } catch (error: any) {
      setError('Failed to get meal recommendations');
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkClaudeStatus();
    fetchRecommendations();
  }, []);

  const handleRefresh = () => {
    fetchRecommendations();
  };

  const handleMealTypeFilter = (mealType: string) => {
    fetchRecommendations({ meal_type: mealType });
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
          {!claudeAvailable && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <AutoAwesome sx={{ mr: 1 }} />
              Using fallback recommendations. Connect Claude API for AI-powered suggestions.
            </Alert>
          )}
        </Box>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Get New Ideas
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Meal Type Filters */}
      <Box mb={3}>
        <Typography variant="h6" gutterBottom>
          Filter by Meal Type
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Button variant="outlined" onClick={() => fetchRecommendations()}>
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
            {claudeAvailable ? 'AI is crafting personalized recommendations...' : 'Loading recommendations...'}
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {recommendations.map((meal, index) => (
            <Grid key={index} size={{ xs: 12, md: 6, lg: 4 }}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" component="h2" gutterBottom>
                      {meal.name}
                    </Typography>
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
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Restaurant />}
                    onClick={() => setSelectedMeal(meal)}
                  >
                    View Recipe
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
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
            <Button variant="contained" onClick={handleRefresh}>
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
              <Button variant="contained" color="primary">
                Add to Meal Plan
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default MealRecommendations;