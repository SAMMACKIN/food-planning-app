import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  TextField,
  Box,
  FormControlLabel,
  Checkbox,
  Alert,
  Chip
} from '@mui/material';
import { Restaurant, Psychology, AutoFixHigh, SmartToy, AutoAwesome } from '@mui/icons-material';
import StarRating from './StarRating';
import { Recipe, RecipeRating } from '../../types';

interface RateRecipeDialogProps {
  open: boolean;
  onClose: () => void;
  recipe: Recipe | null;
  existingRating?: RecipeRating;
  onSubmit: (rating: Omit<RecipeRating, 'id' | 'recipe_id' | 'user_id' | 'created_at' | 'updated_at'>) => Promise<boolean>;
}

const RateRecipeDialog: React.FC<RateRecipeDialogProps> = ({
  open,
  onClose,
  recipe,
  existingRating,
  onSubmit
}) => {
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [wouldMakeAgain, setWouldMakeAgain] = useState(true);
  const [cookingNotes, setCookingNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when dialog opens/closes or recipe changes
  useEffect(() => {
    if (open && recipe) {
      if (existingRating) {
        setRating(existingRating.rating);
        setReviewText(existingRating.review_text || '');
        setWouldMakeAgain(existingRating.would_make_again);
        setCookingNotes(existingRating.cooking_notes || '');
      } else {
        setRating(0);
        setReviewText('');
        setWouldMakeAgain(true);
        setCookingNotes('');
      }
      setError(null);
    }
  }, [open, recipe, existingRating]);

  const handleSubmit = async () => {
    if (!recipe || rating === 0) {
      setError('Please select a star rating');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const ratingData = {
        rating,
        review_text: reviewText.trim() || null,
        would_make_again: wouldMakeAgain,
        cooking_notes: cookingNotes.trim() || null
      };

      const success = await onSubmit(ratingData);
      if (success) {
        onClose();
      } else {
        setError('Failed to save rating. Please try again.');
      }
    } catch (error) {
      console.error('Error submitting rating:', error);
      setError('An error occurred while saving your rating');
    } finally {
      setSubmitting(false);
    }
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

  if (!recipe) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Restaurant color="primary" />
          Rate Recipe: {recipe.name}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Recipe Info */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Recipe Details:
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {recipe.description}
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            <Chip size="small" label={`${recipe.prep_time} min`} />
            <Chip size="small" label={recipe.difficulty} />
            <Chip size="small" label={`${recipe.servings} servings`} />
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
          </Box>
        </Box>

        {/* Star Rating */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Overall Rating *
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <StarRating
              rating={rating}
              onRatingChange={setRating}
              size="large"
            />
            <Typography variant="body2" color="text.secondary">
              {rating === 0 ? 'Select a rating' : 
               rating === 1 ? 'Poor' :
               rating === 2 ? 'Fair' :
               rating === 3 ? 'Good' :
               rating === 4 ? 'Very Good' :
               'Excellent'}
            </Typography>
          </Box>
        </Box>

        {/* Would Make Again */}
        <Box sx={{ mb: 3 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={wouldMakeAgain}
                onChange={(e) => setWouldMakeAgain(e.target.checked)}
                color="primary"
              />
            }
            label="I would make this recipe again"
          />
        </Box>

        {/* Review Text */}
        <Box sx={{ mb: 3 }}>
          <TextField
            label="Review (Optional)"
            multiline
            rows={3}
            fullWidth
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            placeholder="Share your thoughts about this recipe - what did you like? What would you change?"
            helperText={`${reviewText.length}/500 characters`}
            inputProps={{ maxLength: 500 }}
          />
        </Box>

        {/* Cooking Notes */}
        <Box sx={{ mb: 3 }}>
          <TextField
            label="Cooking Notes (Optional)"
            multiline
            rows={2}
            fullWidth
            value={cookingNotes}
            onChange={(e) => setCookingNotes(e.target.value)}
            placeholder="Any modifications you made or tips for next time?"
            helperText={`${cookingNotes.length}/300 characters`}
            inputProps={{ maxLength: 300 }}
          />
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={submitting || rating === 0}
        >
          {submitting ? 'Saving...' : existingRating ? 'Update Rating' : 'Save Rating'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RateRecipeDialog;