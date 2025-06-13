import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
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
} from '@mui/material';
import { Add, Delete, CalendarToday, Restaurant } from '@mui/icons-material';
import { apiRequest } from '../../services/api';

interface MealPlan {
  id: string;
  user_id: string;
  date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  meal_name: string;
  meal_description?: string;
  ingredients: string[];
  created_at: string;
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
    have_in_pantry: boolean;
  }>;
  instructions: string[];
  tags: string[];
  nutrition_notes: string;
  pantry_usage_score: number;
  ai_generated?: boolean;
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

  // Format date for API
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
      setLoading(true);
      const weekDates = getWeekDates();
      const startDate = formatDate(weekDates[0]);
      const endDate = formatDate(weekDates[6]);
      
      // For now, use empty array since we don't have backend endpoints yet
      // TODO: Implement backend endpoints for meal plans
      setMealPlans([]);
      setError(null);
    } catch (error: any) {
      setError('Failed to fetch meal plans');
      console.error('Error fetching meal plans:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch recommendations for meal selection
  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await apiRequest<MealRecommendation[]>('POST', '/recommendations', {
        num_recommendations: 5,
        meal_type: selectedSlot?.mealType,
        preferences: {}
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

      const newMealPlan: MealPlan = {
        id: `temp-${Date.now()}`, // Temporary ID
        user_id: 'current-user', // TODO: Get from auth
        date,
        meal_type: selectedSlot.mealType as any,
        meal_name: recommendation.name,
        meal_description: recommendation.description,
        ingredients: recommendation.ingredients_needed.map(ing => `${ing.quantity} ${ing.unit} ${ing.name}`),
        created_at: new Date().toISOString()
      };

      // TODO: Save to backend
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

    // TODO: Remove from backend
    setMealPlans(prev => prev.filter(p => !(p.date === date && p.meal_type === mealType)));
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(currentWeekStart.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentWeekStart(newDate);
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
            {currentWeekStart.toLocaleDateString()} - {getWeekDates()[6].toLocaleDateString()}
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
      <Grid container spacing={2}>
        {DAYS_OF_WEEK.map((day, dayIndex) => (
          <Grid item xs={12} md={1.71} key={day}>
            <Card>
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
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {meal.meal_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {meal.meal_description}
                              </Typography>
                            </Box>
                            <IconButton 
                              size="small" 
                              onClick={() => handleRemoveMeal(day, mealType)}
                              sx={{ ml: 1 }}
                            >
                              <Delete fontSize="small" />
                            </IconButton>
                          </Box>
                        </Card>
                      ) : (
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          startIcon={<Add />}
                          onClick={() => handleSlotClick(day, mealType)}
                          sx={{ minHeight: 60, border: '2px dashed', borderColor: 'divider' }}
                        >
                          Add Meal
                        </Button>
                      )}
                    </Box>
                  );
                })}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

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
                            <Chip label="AI Generated" size="small" color="primary" />
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
                            {recommendation.tags.map(tag => (
                              <Chip key={tag} label={tag} size="small" variant="outlined" />
                            ))}
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
    </Box>
  );
};

export default MealPlanning;