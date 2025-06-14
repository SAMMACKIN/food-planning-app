import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  Alert,
  TextField,
  Rating,
  FormControlLabel,
  Checkbox,
  Divider,
} from '@mui/material';
import { Add, Delete, CalendarToday, Restaurant, RateReview, Star } from '@mui/icons-material';
import { apiRequest } from '../../services/api';

interface MealPlan {
  id: string;
  date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  meal_name: string;
  meal_description?: string;
  recipe_data?: any;
  ai_generated?: boolean;
  ai_provider?: string;
}

interface MealRecommendation {
  name: string;
  description: string;
  prep_time: number;
  difficulty: string;
  servings: number;
  ingredients_needed: Array<{
    name: string;
    quantity: string;
    unit: string;
  }>;
  instructions: string[];
  tags: string[];
  ai_generated?: boolean;
}

interface MealReview {
  id: string;
  meal_plan_id: string;
  rating: number;
  review_text?: string;
  would_make_again: boolean;
  preparation_notes?: string;
  reviewed_at: string;
}

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'] as const;

const MealPlanning: React.FC = () => {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(getMonday(new Date()));
  const [selectedSlot, setSelectedSlot] = useState<{day: string, mealType: string} | null>(null);
  const [recommendations, setRecommendations] = useState<MealRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewMeal, setReviewMeal] = useState<MealPlan | null>(null);
  const [reviews, setReviews] = useState<MealReview[]>([]);
  const [reviewForm, setReviewForm] = useState({
    rating: 5,
    review_text: '',
    would_make_again: true,
    preparation_notes: ''
  });

  // Get Monday of current week
  function getMonday(date: Date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
  }

  // Get week dates
  const getWeekDates = () => {
    const dates = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(currentWeekStart);
      date.setDate(currentWeekStart.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  // Format date for storage
  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  // Get meal for specific day and type
  const getMealForSlot = (day: string, mealType: string) => {
    const weekDates = getWeekDates();
    const dayIndex = DAYS_OF_WEEK.indexOf(day);
    const date = formatDate(weekDates[dayIndex]);
    
    return mealPlans.find(plan => 
      plan.date === date && plan.meal_type === mealType
    );
  };

  // Fetch meal plans for current week
  const fetchMealPlans = async () => {
    try {
      const weekDates = getWeekDates();
      const startDate = formatDate(weekDates[0]);
      const endDate = formatDate(weekDates[6]);
      
      const response = await apiRequest<MealPlan[]>('GET', `/meal-plans?start_date=${startDate}&end_date=${endDate}`);
      setMealPlans(response);
    } catch (error: any) {
      setError('Failed to fetch meal plans');
      console.error('Error fetching meal plans:', error);
    }
  };

  // Fetch recommendations for meal selection
  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await apiRequest<MealRecommendation[]>('POST', '/recommendations', {
        num_recommendations: 10
      });
      setRecommendations(response);
    } catch (error: any) {
      setError('Failed to fetch recommendations');
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMealPlans();
  }, [currentWeekStart]);

  useEffect(() => {
    if (selectedSlot) {
      fetchRecommendations();
    }
  }, [selectedSlot]);

  const handleSlotClick = (day: string, mealType: string) => {
    setSelectedSlot({ day, mealType });
  };

  const handleAssignMeal = async (recommendation: MealRecommendation) => {
    if (!selectedSlot) return;

    try {
      const weekDates = getWeekDates();
      const dayIndex = DAYS_OF_WEEK.indexOf(selectedSlot.day);
      const date = formatDate(weekDates[dayIndex]);

      const mealPlanData = {
        date,
        meal_type: selectedSlot.mealType,
        meal_name: recommendation.name,
        meal_description: recommendation.description,
        recipe_data: {
          prep_time: recommendation.prep_time,
          difficulty: recommendation.difficulty,
          servings: recommendation.servings,
          ingredients_needed: recommendation.ingredients_needed,
          instructions: recommendation.instructions,
          tags: recommendation.tags,
          nutrition_notes: recommendation.nutrition_notes,
          pantry_usage_score: recommendation.pantry_usage_score
        },
        ai_generated: recommendation.ai_generated,
        ai_provider: recommendation.ai_provider
      };

      const newMealPlan = await apiRequest<MealPlan>('POST', '/meal-plans', mealPlanData);
      
      // Update local state
      setMealPlans(prev => [...prev.filter(p => !(p.date === date && p.meal_type === selectedSlot.mealType)), newMealPlan]);
      setSelectedSlot(null);
    } catch (error: any) {
      setError('Failed to assign meal');
      console.error('Error assigning meal:', error);
    }
  };

  const handleRemoveMeal = async (day: string, mealType: string) => {
    const weekDates = getWeekDates();
    const dayIndex = DAYS_OF_WEEK.indexOf(day);
    const date = formatDate(weekDates[dayIndex]);

    const meal = mealPlans.find(p => p.date === date && p.meal_type === mealType);
    if (!meal) return;

    try {
      await apiRequest('DELETE', `/meal-plans/${meal.id}`);
      setMealPlans(prev => prev.filter(p => !(p.date === date && p.meal_type === mealType)));
    } catch (error: any) {
      setError('Failed to remove meal');
      console.error('Error removing meal:', error);
    }
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(currentWeekStart.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentWeekStart(newDate);
  };

  const handleReviewMeal = async (meal: MealPlan) => {
    setReviewMeal(meal);
    try {
      const response = await apiRequest<MealReview[]>('GET', `/meal-plans/${meal.id}/reviews`);
      setReviews(response);
    } catch (error: any) {
      console.error('Error fetching reviews:', error);
    }
  };

  const handleSubmitReview = async () => {
    if (!reviewMeal) return;

    try {
      const newReview = await apiRequest<MealReview>('POST', `/meal-plans/${reviewMeal.id}/reviews`, reviewForm);
      setReviews(prev => [newReview, ...prev]);
      setReviewForm({
        rating: 5,
        review_text: '',
        would_make_again: true,
        preparation_notes: ''
      });
    } catch (error: any) {
      setError('Failed to submit review');
      console.error('Error submitting review:', error);
    }
  };

  const closeReviewModal = () => {
    setReviewMeal(null);
    setReviews([]);
    setReviewForm({
      rating: 5,
      review_text: '',
      would_make_again: true,
      preparation_notes: ''
    });
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          <CalendarToday sx={{ mr: 1, verticalAlign: 'middle' }} />
          Meal Planning
        </Typography>
        
        <Box display="flex" alignItems="center" gap={2}>
          <Button variant="outlined" onClick={() => navigateWeek('prev')}>
            Previous Week
          </Button>
          <Typography variant="h6">
            Week of {currentWeekStart.toLocaleDateString()}
          </Typography>
          <Button variant="outlined" onClick={() => navigateWeek('next')}>
            Next Week
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Calendar Grid */}
      <Box 
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(3, 1fr)',
            lg: 'repeat(7, 1fr)'
          },
          gap: 2
        }}
      >
        {DAYS_OF_WEEK.map((day, dayIndex) => (
          <Card key={day} sx={{ height: 'fit-content' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom textAlign="center">
                {day}
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center" mb={2}>
                {getWeekDates()[dayIndex].getDate()}
              </Typography>

              {MEAL_TYPES.map(mealType => {
                const meal = getMealForSlot(day, mealType);
                return (
                  <Box key={mealType} mb={2}>
                    <Typography variant="body2" fontWeight="bold" mb={1}>
                      {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
                    </Typography>
                    {meal ? (
                      <Card variant="outlined" sx={{ p: 1, bgcolor: 'primary.50' }}>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box flex={1}>
                            <Typography variant="body2" fontWeight="bold" noWrap>
                              {meal.meal_name}
                            </Typography>
                            {meal.meal_description && (
                              <Typography variant="caption" color="text.secondary" noWrap>
                                {meal.meal_description}
                              </Typography>
                            )}
                            {meal.ai_generated && (
                              <Chip 
                                label={meal.ai_provider || 'AI'} 
                                size="small" 
                                color="primary" 
                                sx={{ mt: 0.5, height: 16, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                          <Box display="flex" flexDirection="column" gap={0.5}>
                            <IconButton 
                              size="small" 
                              onClick={() => handleReviewMeal(meal)}
                              title="Review this meal"
                            >
                              <RateReview fontSize="small" />
                            </IconButton>
                            <IconButton 
                              size="small" 
                              onClick={() => handleRemoveMeal(day, mealType)}
                              title="Remove meal"
                            >
                              <Delete fontSize="small" />
                            </IconButton>
                          </Box>
                        </Box>
                      </Card>
                    ) : (
                      <Button
                        variant="outlined"
                        size="small"
                        fullWidth
                        startIcon={<Add />}
                        onClick={() => handleSlotClick(day, mealType)}
                        sx={{ 
                          minHeight: 50, 
                          border: '2px dashed', 
                          borderColor: 'divider',
                          '&:hover': {
                            borderColor: 'primary.main'
                          }
                        }}
                      >
                        Add
                      </Button>
                    )}
                  </Box>
                );
              })}
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Meal Selection Dialog */}
      <Dialog 
        open={!!selectedSlot} 
        onClose={() => setSelectedSlot(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Choose a meal for {selectedSlot?.day} {selectedSlot?.mealType}
        </DialogTitle>
        <DialogContent>
          {loading ? (
            <Typography>Loading recommendations...</Typography>
          ) : (
            <List>
              {recommendations.map((recommendation, index) => (
                <ListItem key={index} disablePadding>
                  <ListItemButton onClick={() => handleAssignMeal(recommendation)}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Restaurant />
                          <Typography variant="h6">{recommendation.name}</Typography>
                          {recommendation.ai_generated && (
                            <Chip label="AI" size="small" color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" mb={1}>
                            {recommendation.description}
                          </Typography>
                          <Box display="flex" gap={1} flexWrap="wrap">
                            <Chip label={`${recommendation.prep_time} min`} size="small" />
                            <Chip label={recommendation.difficulty} size="small" />
                            <Chip label={`${recommendation.servings} servings`} size="small" />
                          </Box>
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedSlot(null)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Meal Review Dialog */}
      <Dialog 
        open={!!reviewMeal} 
        onClose={closeReviewModal}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <RateReview />
            Review: {reviewMeal?.meal_name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {reviewMeal && (
            <Box>
              {/* Meal Details */}
              <Card variant="outlined" sx={{ mb: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {reviewMeal.meal_name}
                </Typography>
                {reviewMeal.meal_description && (
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    {reviewMeal.meal_description}
                  </Typography>
                )}
                {reviewMeal.recipe_data && (
                  <Box>
                    <Box display="flex" gap={1} mb={1}>
                      <Chip label={`${reviewMeal.recipe_data.prep_time} min`} size="small" />
                      <Chip label={reviewMeal.recipe_data.difficulty} size="small" />
                      <Chip label={`${reviewMeal.recipe_data.servings} servings`} size="small" />
                    </Box>
                    {reviewMeal.ai_generated && (
                      <Chip 
                        label={`AI Generated (${reviewMeal.ai_provider})`} 
                        size="small" 
                        color="primary"
                      />
                    )}
                  </Box>
                )}
              </Card>

              {/* Existing Reviews */}
              {reviews.length > 0 && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Previous Reviews
                  </Typography>
                  {reviews.map((review) => (
                    <Card key={review.id} variant="outlined" sx={{ mb: 2, p: 2 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Rating value={review.rating} readOnly size="small" />
                        <Typography variant="body2" color="text.secondary">
                          {new Date(review.reviewed_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                      {review.review_text && (
                        <Typography variant="body2" mb={1}>
                          {review.review_text}
                        </Typography>
                      )}
                      <Box display="flex" gap={1}>
                        <Chip 
                          label={review.would_make_again ? "Would make again" : "Wouldn't make again"} 
                          size="small" 
                          color={review.would_make_again ? "success" : "default"}
                        />
                      </Box>
                      {review.preparation_notes && (
                        <Typography variant="caption" color="text.secondary" mt={1} display="block">
                          Notes: {review.preparation_notes}
                        </Typography>
                      )}
                    </Card>
                  ))}
                  <Divider sx={{ my: 2 }} />
                </Box>
              )}

              {/* New Review Form */}
              <Typography variant="h6" gutterBottom>
                Add Your Review
              </Typography>
              <Box component="form">
                <Box mb={2}>
                  <Typography component="legend" gutterBottom>
                    Rating
                  </Typography>
                  <Rating
                    value={reviewForm.rating}
                    onChange={(event, newValue) => 
                      setReviewForm(prev => ({ ...prev, rating: newValue || 1 }))
                    }
                  />
                </Box>

                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Review"
                  placeholder="How was this meal? What did you like or dislike?"
                  value={reviewForm.review_text}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, review_text: e.target.value }))}
                  sx={{ mb: 2 }}
                />

                <FormControlLabel
                  control={
                    <Checkbox
                      checked={reviewForm.would_make_again}
                      onChange={(e) => setReviewForm(prev => ({ ...prev, would_make_again: e.target.checked }))}
                    />
                  }
                  label="I would make this meal again"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Preparation Notes"
                  placeholder="Any tips or modifications you made while cooking..."
                  value={reviewForm.preparation_notes}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, preparation_notes: e.target.value }))}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeReviewModal}>Cancel</Button>
          <Button onClick={handleSubmitReview} variant="contained">
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MealPlanning;