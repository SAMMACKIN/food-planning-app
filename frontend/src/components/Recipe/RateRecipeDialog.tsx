import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import { RecipeRatingCreate } from '../../types';
import StarRating from './StarRating';

interface RateRecipeDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (rating: RecipeRatingCreate) => Promise<void>;
  recipeId: string;
  recipeName: string;
  loading?: boolean;
  error?: string | null;
}

const RateRecipeDialog: React.FC<RateRecipeDialogProps> = ({
  open,
  onClose,
  onSubmit,
  recipeId,
  recipeName,
  loading = false,
  error
}) => {
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [wouldMakeAgain, setWouldMakeAgain] = useState(true);
  const [cookingNotes, setCookingNotes] = useState('');
  
  const handleSubmit = async () => {
    const ratingData: RecipeRatingCreate = {
      recipe_id: recipeId,
      rating,
      review_text: reviewText.trim() || undefined,
      would_make_again: wouldMakeAgain,
      cooking_notes: cookingNotes.trim() || undefined,
    };
    
    await onSubmit(ratingData);
  };

  const handleClose = () => {
    if (!loading) {
      // Reset form
      setRating(5);
      setReviewText('');
      setWouldMakeAgain(true);
      setCookingNotes('');
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        Rate Recipe: {recipeName}
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>
            Overall Rating *
          </Typography>
          <StarRating
            rating={rating}
            onChange={setRating}
            size="large"
            showValue
          />
        </Box>

        <TextField
          label="Review (optional)"
          multiline
          rows={3}
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
          placeholder="What did you think of this recipe?"
          fullWidth
          sx={{ mb: 2 }}
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={wouldMakeAgain}
              onChange={(e) => setWouldMakeAgain(e.target.checked)}
            />
          }
          label="I would make this recipe again"
          sx={{ mb: 2 }}
        />

        <TextField
          label="Cooking Notes (optional)"
          multiline
          rows={2}
          value={cookingNotes}
          onChange={(e) => setCookingNotes(e.target.value)}
          placeholder="Any modifications or tips for next time?"
          fullWidth
        />
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || rating === 0}
        >
          {loading ? 'Submitting...' : 'Submit Rating'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RateRecipeDialog;