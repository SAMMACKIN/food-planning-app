import React, { useState } from 'react';
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
} from '@mui/icons-material';
import { useRecipes } from '../../hooks/useRecipes';
import { Recipe } from '../../types';
import RecipeInstructions from '../../components/Recipe/RecipeInstructions';
import CreateRecipeForm from '../../components/Recipe/CreateRecipeForm';

const SavedRecipes: React.FC = () => {
  const {
    savedRecipes,
    loading,
    error,
    fetchSavedRecipes,
    deleteRecipe,
    saveRecipe,
    clearError
  } = useRecipes();

  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuRecipeId, setMenuRecipeId] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [createRecipeDialogOpen, setCreateRecipeDialogOpen] = useState(false);

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

  // Rating functionality temporarily removed (no ratings in RecipeV2)

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
            <Grid key={recipe.id} size={{ xs: 12, md: 6, lg: 4 }}>
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

      {/* Rating functionality temporarily removed */}

      {/* Create Recipe Dialog */}
      <CreateRecipeForm
        open={createRecipeDialogOpen}
        onClose={() => setCreateRecipeDialogOpen(false)}
        onSave={handleCreateCustomRecipe}
      />
    </Box>
  );
};

export default SavedRecipes;