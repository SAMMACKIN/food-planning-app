import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert,
} from '@mui/material';
import { Add, Delete, Restaurant, Timer, People, Link as LinkIcon, Close as CloseIcon } from '@mui/icons-material';
import { RecipeCreate, IngredientNeeded } from '../../types';

interface CreateRecipeFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (recipe: RecipeCreate) => Promise<boolean>;
}

const DIFFICULTY_OPTIONS = ['Easy', 'Medium', 'Hard'];
const COMMON_TAGS = [
  'Quick & Easy', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', 'Low-Carb',
  'High-Protein', 'Dairy-Free', 'Spicy', 'Sweet', 'Savory', 'Comfort Food',
  'Healthy', 'Kid-Friendly', 'One-Pot', 'Meal Prep', 'Budget-Friendly'
];

const CreateRecipeForm: React.FC<CreateRecipeFormProps> = ({ open, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prep_time: 30,
    difficulty: 'Easy',
    servings: 4,
    nutrition_notes: ''
  });

  const [ingredients, setIngredients] = useState<IngredientNeeded[]>([]);
  const [instructions, setInstructions] = useState<string[]>(['']);
  const [tags, setTags] = useState<string[]>([]);
  const [newIngredient, setNewIngredient] = useState({
    name: '',
    quantity: '',
    unit: ''
  });
  const [newTag, setNewTag] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importMode, setImportMode] = useState(false);
  const [importUrl, setImportUrl] = useState('');
  const [importLoading, setImportLoading] = useState(false);

  const handleAddIngredient = () => {
    if (newIngredient.name && newIngredient.quantity && newIngredient.unit) {
      setIngredients(prev => [...prev, {
        ...newIngredient,
        have_in_pantry: false // Default to false for user-added ingredients
      }]);
      setNewIngredient({ name: '', quantity: '', unit: '' });
    }
  };

  const handleRemoveIngredient = (index: number) => {
    setIngredients(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddInstruction = () => {
    setInstructions(prev => [...prev, '']);
  };

  const handleUpdateInstruction = (index: number, value: string) => {
    setInstructions(prev => prev.map((instruction, i) => 
      i === index ? value : instruction
    ));
  };

  const handleRemoveInstruction = (index: number) => {
    if (instructions.length > 1) {
      setInstructions(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleAddTag = (tag: string) => {
    if (tag && !tags.includes(tag)) {
      setTags(prev => [...prev, tag]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  const handleSubmit = async () => {
    setError(null);
    
    // Validation
    if (!formData.name || !formData.description) {
      setError('Please fill in recipe name and description');
      return;
    }
    
    if (ingredients.length === 0) {
      setError('Please add at least one ingredient');
      return;
    }
    
    if (instructions.filter(i => i.trim()).length === 0) {
      setError('Please add at least one instruction step');
      return;
    }

    setLoading(true);
    
    const recipeData: RecipeCreate = {
      ...formData,
      ingredients_needed: ingredients,
      instructions: instructions.filter(i => i.trim()), // Remove empty instructions
      tags,
      pantry_usage_score: 0, // Default for user-created recipes
      ai_generated: false,
      source: 'user_created'
    };

    const success = await onSave(recipeData);
    
    if (success) {
      handleReset();
      onClose();
    }
    
    setLoading(false);
  };

  const handleImportFromUrl = async () => {
    if (!importUrl.trim()) {
      setError('Please enter a URL');
      return;
    }

    setImportLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/recipes/import-from-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ url: importUrl.trim() })
      });

      if (!response.ok) {
        let errorMessage = 'Failed to import recipe';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (jsonError) {
          // If error response isn't JSON, use status text
          errorMessage = response.statusText || `HTTP ${response.status}`;
        }
        throw new Error(errorMessage);
      }

      let result;
      try {
        result = await response.json();
      } catch (jsonError) {
        console.error('Failed to parse JSON response:', jsonError);
        throw new Error('Server returned invalid response. Please try again.');
      }
      const recipeData = result.recipe_data;

      // Populate form with imported data
      setFormData({
        name: recipeData.name || '',
        description: recipeData.description || '',
        prep_time: recipeData.prep_time || 30,
        difficulty: recipeData.difficulty || 'Medium',
        servings: recipeData.servings || 4,
        nutrition_notes: recipeData.nutrition_notes || ''
      });

      setIngredients(recipeData.ingredients_needed || []);
      setInstructions(recipeData.instructions || ['']);
      setTags(recipeData.tags || []);

      setImportMode(false);
      setImportUrl('');
      
      // Show success message
      setError(null);
      
    } catch (error: any) {
      console.error('Import error:', error);
      setError(error.message || 'Failed to import recipe from URL');
    } finally {
      setImportLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: '',
      description: '',
      prep_time: 30,
      difficulty: 'Easy',
      servings: 4,
      nutrition_notes: ''
    });
    setIngredients([]);
    setInstructions(['']);
    setTags([]);
    setNewIngredient({ name: '', quantity: '', unit: '' });
    setNewTag('');
    setError(null);
    setImportMode(false);
    setImportUrl('');
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <Restaurant color="primary" />
            <Typography variant="h6">Create Your Own Recipe</Typography>
          </Box>
          <Button 
            variant="outlined" 
            size="small"
            startIcon={<LinkIcon />}
            onClick={() => setImportMode(!importMode)}
            disabled={loading || importLoading}
          >
            {importMode ? 'Manual Entry' : 'Import from URL'}
          </Button>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {/* URL Import Section */}
        {importMode && (
          <Box mb={3} p={2} border={1} borderColor="primary.main" borderRadius={2} bgcolor="primary.50">
            <Typography variant="h6" gutterBottom color="primary.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LinkIcon />
              Import Recipe from URL
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Paste a link to any recipe website and we'll automatically extract the details for you.
            </Typography>
            
            <Box display="flex" gap={1} mt={2}>
              <TextField
                fullWidth
                label="Recipe URL"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                placeholder="https://example.com/recipe"
                disabled={importLoading}
                onKeyPress={(e) => e.key === 'Enter' && handleImportFromUrl()}
              />
              <Button 
                variant="contained" 
                onClick={handleImportFromUrl}
                disabled={!importUrl.trim() || importLoading}
                sx={{ minWidth: 120 }}
              >
                {importLoading ? 'Importing...' : 'Import'}
              </Button>
            </Box>
            
            {importLoading && (
              <Box mt={2} display="flex" alignItems="center" gap={1}>
                <Typography variant="body2" color="text.secondary">
                  🤖 AI is extracting recipe details from the webpage...
                </Typography>
              </Box>
            )}
          </Box>
        )}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Basic Information */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>Basic Information</Typography>
          
          <TextField
            fullWidth
            label="Recipe Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mb: 2 }}
            required
          />
          
          <TextField
            fullWidth
            multiline
            rows={2}
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            sx={{ mb: 2 }}
            required
          />
          
          <Box display="flex" gap={2} mb={2}>
            <TextField
              label="Prep Time (minutes)"
              type="number"
              value={formData.prep_time}
              onChange={(e) => setFormData(prev => ({ ...prev, prep_time: parseInt(e.target.value) || 30 }))}
              InputProps={{ startAdornment: <Timer fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> }}
              sx={{ flex: 1 }}
            />
            
            <FormControl sx={{ flex: 1 }}>
              <InputLabel>Difficulty</InputLabel>
              <Select
                value={formData.difficulty}
                label="Difficulty"
                onChange={(e) => setFormData(prev => ({ ...prev, difficulty: e.target.value }))}
              >
                {DIFFICULTY_OPTIONS.map(option => (
                  <MenuItem key={option} value={option}>{option}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              label="Servings"
              type="number"
              value={formData.servings}
              onChange={(e) => setFormData(prev => ({ ...prev, servings: parseInt(e.target.value) || 4 }))}
              InputProps={{ startAdornment: <People fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> }}
              sx={{ flex: 1 }}
            />
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Ingredients */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>Ingredients</Typography>
          
          <Box display="flex" gap={1} mb={2}>
            <TextField
              label="Ingredient"
              value={newIngredient.name}
              onChange={(e) => setNewIngredient(prev => ({ ...prev, name: e.target.value }))}
              sx={{ flex: 2 }}
            />
            <TextField
              label="Amount"
              value={newIngredient.quantity}
              onChange={(e) => setNewIngredient(prev => ({ ...prev, quantity: e.target.value }))}
              sx={{ flex: 1 }}
            />
            <TextField
              label="Unit"
              value={newIngredient.unit}
              onChange={(e) => setNewIngredient(prev => ({ ...prev, unit: e.target.value }))}
              sx={{ flex: 1 }}
              placeholder="cup, tsp, etc."
            />
            <Button 
              variant="outlined" 
              onClick={handleAddIngredient}
              disabled={!newIngredient.name || !newIngredient.quantity || !newIngredient.unit}
            >
              <Add />
            </Button>
          </Box>
          
          {ingredients.length > 0 && (
            <List dense>
              {ingredients.map((ingredient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={`${ingredient.quantity} ${ingredient.unit} ${ingredient.name}`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton edge="end" onClick={() => handleRemoveIngredient(index)}>
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Instructions */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>Instructions</Typography>
          
          {instructions.map((instruction, index) => (
            <Box key={index} display="flex" gap={1} mb={2} alignItems="flex-start">
              <Typography variant="body2" sx={{ 
                minWidth: 30, 
                mt: 2, 
                fontWeight: 'bold',
                color: 'primary.main'
              }}>
                {index + 1}.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={2}
                value={instruction}
                onChange={(e) => handleUpdateInstruction(index, e.target.value)}
                placeholder={`Step ${index + 1}: Describe what to do...`}
              />
              <IconButton 
                onClick={() => handleRemoveInstruction(index)}
                disabled={instructions.length === 1}
                sx={{ mt: 1 }}
              >
                <Delete />
              </IconButton>
            </Box>
          ))}
          
          <Button variant="outlined" onClick={handleAddInstruction} startIcon={<Add />}>
            Add Step
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Tags */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>Tags</Typography>
          
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Quick add:
            </Typography>
            <Box display="flex" gap={0.5} flexWrap="wrap" mb={2}>
              {COMMON_TAGS.filter(tag => !tags.includes(tag)).slice(0, 8).map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  onClick={() => handleAddTag(tag)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>
          
          <Box display="flex" gap={1} mb={2}>
            <TextField
              label="Custom Tag"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddTag(newTag)}
              sx={{ flex: 1 }}
            />
            <Button 
              variant="outlined" 
              onClick={() => handleAddTag(newTag)}
              disabled={!newTag || tags.includes(newTag)}
            >
              <Add />
            </Button>
          </Box>
          
          {tags.length > 0 && (
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {tags.map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleRemoveTag(tag)}
                  size="small"
                />
              ))}
            </Box>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Nutrition Notes */}
        <Box>
          <Typography variant="h6" gutterBottom>Nutrition Notes (Optional)</Typography>
          <TextField
            fullWidth
            multiline
            rows={2}
            label="Nutrition Information"
            value={formData.nutrition_notes}
            onChange={(e) => setFormData(prev => ({ ...prev, nutrition_notes: e.target.value }))}
            placeholder="e.g., High in protein, Low in carbs, Contains nuts, etc."
          />
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save Recipe'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateRecipeForm;