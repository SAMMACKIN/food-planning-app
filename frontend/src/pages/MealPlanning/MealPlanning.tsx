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
  date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  meal_name: string;
  meal_description?: string;
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

  // Fetch recommendations for meal selection
  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await apiRequest<MealRecommendation[]>('POST', '/recommendations', {
        num_recommendations: 5
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
        id: `temp-${Date.now()}`,
        date,
        meal_type: selectedSlot.mealType as any,
        meal_name: recommendation.name,
        meal_description: recommendation.description
      };

      // Store locally for now (TODO: Save to backend)
      setMealPlans(prev => [...prev.filter(p => !(p.date === date && p.meal_type === selectedSlot.mealType)), newMealPlan]);
      setSelectedSlot(null);
    } catch (error: any) {
      setError('Failed to assign meal');
    }
  };

  const handleRemoveMeal = (day: string, mealType: string) => {
    const weekDates = getWeekDates();
    const dayIndex = DAYS_OF_WEEK.indexOf(day);
    const date = formatDate(weekDates[dayIndex]);

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
      <Grid container spacing={2}>
        {DAYS_OF_WEEK.map((day, dayIndex) => (
          <Grid item xs={12} sm={6} md={4} lg={12/7} xl={12/7} key={day}>
            <Card sx={{ height: '100%' }}>
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
                            </Box>
                            <IconButton 
                              size="small" 
                              onClick={() => handleRemoveMeal(day, mealType)}
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
    </Box>
  );
};

export default MealPlanning;