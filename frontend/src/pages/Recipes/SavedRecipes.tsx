import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  TextField,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Timer,
  People,
  Delete,
  MoreVert,
  CalendarToday,
  Refresh,
  Search,
  FilterList,
  Add,
  MenuBook,
  Star,
  Psychology,
  AutoFixHigh,
  SmartToy,
  AutoAwesome,
  Link,
  Edit,
} from '@mui/icons-material';
import { useRecipes } from '../../hooks/useRecipes';
import { useAuthStore } from '../../store/authStore';
import { apiRequest } from '../../services/api';
import { Recipe, RecipeRating } from '../../types';
import RecipeInstructions from '../../components/Recipe/RecipeInstructions';
import CreateRecipeForm from '../../components/Recipe/CreateRecipeForm';
import RateRecipeDialog from '../../components/Recipe/RateRecipeDialog';

const SavedRecipes: React.FC = () => {
  const { user } = useAuthStore();
  const {
    savedRecipes,
    loading,
    error,
    fetchSavedRecipes,
    deleteRecipe,
    saveRecipe,
    updateRecipe,
    createRecipeRating,
    getRecipeRatings,
    updateRecipeRating,
    clearError
  } = useRecipes();

  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuRecipeId, setMenuRecipeId] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [createRecipeDialogOpen, setCreateRecipeDialogOpen] = useState(false);
  const [editRecipeDialogOpen, setEditRecipeDialogOpen] = useState(false);
  // Rating dialog state
  const [ratingDialogOpen, setRatingDialogOpen] = useState(false);
  const [recipeToRate, setRecipeToRate] = useState<Recipe | null>(null);
  const [existingRating, setExistingRating] = useState<RecipeRating | undefined>(undefined);
  // Health check state
  const [healthStatus, setHealthStatus] = useState<string | null>(null);

  const handleViewRecipe = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setDialogOpen(true);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, recipeId: string) => {
    setMenuAnchorEl(event.currentTarget);
    setMenuRecipeId(recipeId);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuRecipeId('');
  };

  const handleDeleteRecipe = async () => {
    if (menuRecipeId) {
      await deleteRecipe(menuRecipeId);
      handleMenuClose();
    }
  };

  const handleOpenRatingDialog = async (recipe: Recipe) => {
    try {
      console.log('🔍 Opening rating dialog for recipe:', recipe.id);
      console.log('👤 Current user ID:', user?.id);
      
      const ratings = await getRecipeRatings(recipe.id);
      console.log('⭐ Found ratings:', ratings);
      
      // Find the current user's rating for this recipe
      const userRating = ratings.find(r => r.user_id === user?.id);
      console.log('👤 User rating found:', userRating);
      
      setExistingRating(userRating);
      setRecipeToRate(recipe);
      setRatingDialogOpen(true);
    } catch (error) {
      console.error('❌ Error loading existing rating:', error);
      setExistingRating(undefined);
      setRecipeToRate(recipe);
      setRatingDialogOpen(true);
    }
  };

  const handleSubmitRating = async (ratingData: Omit<RecipeRating, 'id' | 'recipe_id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<boolean> => {
    if (!recipeToRate) return false;
    
    let success = false;
    if (existingRating) {
      // Update existing rating
      const updatedRating = await updateRecipeRating(recipeToRate.id, existingRating.id, ratingData);
      success = !!updatedRating;
    } else {
      // Create new rating
      const newRating = await createRecipeRating(recipeToRate.id, ratingData);
      success = !!newRating;
    }
    
    if (success) {
      // Refresh recipes to show updated rating data
      fetchSavedRecipes();
    }
    
    return success;
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

  const handleSearch = () => {
    fetchSavedRecipes(searchTerm, difficultyFilter);
  };

  const handleCreateCustomRecipe = async (recipeData: any): Promise<boolean> => {
    const result = await saveRecipe(recipeData);
    if (result) {
      setCreateRecipeDialogOpen(false);
      return true;
    }
    return false;
  };

  const handleUpdateRecipe = async (recipeData: any): Promise<boolean> => {
    if (!selectedRecipe) return false;
    
    const result = await updateRecipe(selectedRecipe.id, recipeData);
    if (result) {
      setEditRecipeDialogOpen(false);
      setSelectedRecipe(null);
      return true;
    }
    return false;
  };

  const performHealthCheck = async () => {
    try {
      console.log('🏥 Running recipes health check...');
      const health = await apiRequest<any>('GET', '/recipes/debug/health');
      console.log('✅ Health check response:', health);
      setHealthStatus(`✅ Healthy - ${health.user_recipe_count} recipes found`);
    } catch (error: any) {
      console.error('❌ Health check failed:', error);
      setHealthStatus(`❌ Unhealthy - ${error.response?.status || 'Network Error'}`);
    }
  };

  // Perform health check on mount
  useEffect(() => {
    if (user?.id) {
      performHealthCheck();
    }
  }, [user?.id]);

  const filteredRecipes = savedRecipes.filter(recipe =>
    recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recipe.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading && savedRecipes.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading your saved recipes...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MenuBook color="primary" />
          Saved Recipes
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateRecipeDialogOpen(true)}
          >
            Create Recipe
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => fetchSavedRecipes()}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={clearError}>
          {error}
        </Alert>
      )}

      {healthStatus && (
        <Alert 
          severity={healthStatus.includes('✅') ? 'success' : 'warning'} 
          sx={{ mb: 2 }} 
          onClose={() => setHealthStatus(null)}
        >
          {healthStatus}
        </Alert>
      )}

      {/* Search and Filter */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          label="Search recipes"
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ flexGrow: 1 }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Difficulty</InputLabel>
          <Select
            value={difficultyFilter}
            label="Difficulty"
            onChange={(e) => setDifficultyFilter(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="Easy">Easy</MenuItem>
            <MenuItem value="Medium">Medium</MenuItem>
            <MenuItem value="Hard">Hard</MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="contained"
          startIcon={<FilterList />}
          onClick={handleSearch}
        >
          Search
        </Button>
      </Box>

      {filteredRecipes.length === 0 ? (
        <Alert severity="info">
          {savedRecipes.length === 0 
            ? "You haven't saved any recipes yet. Go to Recommendations to find and save some recipes!"
            : "No recipes match your search criteria."
          }
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredRecipes.map((recipe) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={recipe.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3" sx={{ flexGrow: 1 }}>
                      {recipe.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, recipe.id)}
                    >
                      <MoreVert />
                    </IconButton>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {recipe.description}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Timer fontSize="small" color="action" />
                      <Typography variant="body2">{recipe.prep_time} min</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <People fontSize="small" color="action" />
                      <Typography variant="body2">{recipe.servings} servings</Typography>
                    </Box>
                    <Chip
                      label={recipe.difficulty}
                      size="small"
                      color={
                        recipe.difficulty === 'Easy' ? 'success' :
                        recipe.difficulty === 'Medium' ? 'warning' : 'error'
                      }
                    />
                    {recipe.ai_provider && (
                      <Chip
                        icon={React.createElement(getAIProviderInfo(recipe.ai_provider).icon)}
                        label={getAIProviderInfo(recipe.ai_provider).name}
                        size="small"
                        sx={{ 
                          backgroundColor: getAIProviderInfo(recipe.ai_provider).color + '20',
                          color: getAIProviderInfo(recipe.ai_provider).color,
                          '& .MuiChip-icon': {
                            color: getAIProviderInfo(recipe.ai_provider).color
                          }
                        }}
                      />
                    )}
                    {recipe.source && 
                      recipe.source !== 'user_created' && 
                      recipe.source !== 'recommendation' &&
                      recipe.source !== 'imported' &&
                      (recipe.source.startsWith('http://') || recipe.source.startsWith('https://')) && (
                      <Chip
                        icon={<Link />}
                        label="View Original"
                        size="small"
                        clickable
                        onClick={() => window.open(recipe.source, '_blank')}
                        sx={{ 
                          backgroundColor: '#2196F3' + '20',
                          color: '#2196F3',
                          '& .MuiChip-icon': {
                            color: '#2196F3'
                          },
                          '&:hover': {
                            backgroundColor: '#2196F3' + '40'
                          }
                        }}
                      />
                    )}
                  </Box>

                  {recipe.tags && recipe.tags.length > 0 && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                      {recipe.tags.slice(0, 3).map((tag, index) => (
                        <Chip key={index} label={tag} size="small" variant="outlined" />
                      ))}
                      {recipe.tags.length > 3 && (
                        <Chip label={`+${recipe.tags.length - 3} more`} size="small" variant="outlined" />
                      )}
                    </Box>
                  )}

                  {/* Cooking statistics removed (not available in RecipeV2) */}

                  <Button
                    variant="contained"
                    fullWidth
                    onClick={() => handleViewRecipe(recipe)}
                    sx={{ mt: 'auto' }}
                  >
                    View Recipe
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Recipe Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          const recipe = savedRecipes.find(r => r.id === menuRecipeId);
          if (recipe) {
            handleOpenRatingDialog(recipe);
          }
          handleMenuClose();
        }}>
          <Star sx={{ mr: 1 }} />
          Rate Recipe
        </MenuItem>
        <MenuItem onClick={() => {
          const recipe = savedRecipes.find(r => r.id === menuRecipeId);
          if (recipe) {
            setSelectedRecipe(recipe);
            setEditRecipeDialogOpen(true);
          }
          handleMenuClose();
        }}>
          <Edit sx={{ mr: 1 }} />
          Edit Recipe
        </MenuItem>
        <MenuItem onClick={() => {/* TODO: Add to meal plan */}}>
          <CalendarToday sx={{ mr: 1 }} />
          Add to Meal Plan
        </MenuItem>
        <MenuItem onClick={handleDeleteRecipe} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete Recipe
        </MenuItem>
      </Menu>

      {/* Recipe Detail Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedRecipe && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5">{selectedRecipe.name}</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label={selectedRecipe.difficulty} size="small" />
                  <Chip label={`${selectedRecipe.prep_time} min`} size="small" />
                  <Chip label={`${selectedRecipe.servings} servings`} size="small" />
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Ingredients:</Typography>
                {selectedRecipe.ingredients_needed.map((ingredient, index) => (
                  <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                    • {ingredient.quantity} {ingredient.unit} {ingredient.name}
                  </Typography>
                ))}
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Instructions:</Typography>
                <RecipeInstructions
                  instructions={selectedRecipe.instructions}
                  prepTime={selectedRecipe.prep_time}
                />
              </Box>
              
              {selectedRecipe.nutrition_notes && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>Nutrition Notes:</Typography>
                  <Typography variant="body2">{selectedRecipe.nutrition_notes}</Typography>
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>Close</Button>
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
          setExistingRating(undefined);
        }}
        recipe={recipeToRate}
        existingRating={existingRating}
        onSubmit={handleSubmitRating}
      />

      {/* Create Recipe Dialog */}
      <CreateRecipeForm
        open={createRecipeDialogOpen}
        onClose={() => setCreateRecipeDialogOpen(false)}
        onSave={handleCreateCustomRecipe}
      />

      {/* Edit Recipe Dialog */}
      <CreateRecipeForm
        open={editRecipeDialogOpen}
        onClose={() => {
          setEditRecipeDialogOpen(false);
          setSelectedRecipe(null);
        }}
        onSave={handleUpdateRecipe}
        initialData={selectedRecipe}
        isEdit={true}
      />
    </Box>
  );
};

export default SavedRecipes;