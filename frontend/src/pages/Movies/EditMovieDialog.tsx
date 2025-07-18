import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Movie as MovieIcon } from '@mui/icons-material';
import { Movie, MovieUpdate, ViewingStatus } from '../../types';

interface EditMovieDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (movieData: MovieUpdate) => Promise<boolean>;
  movie: Movie | null;
}

const EditMovieDialog: React.FC<EditMovieDialogProps> = ({ open, onClose, onSave, movie }) => {
  const [movieData, setMovieData] = useState<MovieUpdate>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (movie) {
      setMovieData({
        title: movie.title,
        description: movie.description,
        genre: movie.genre,
        director: movie.director,
        release_year: movie.release_year,
        runtime: movie.runtime,
        poster_image_url: movie.poster_image_url,
        viewing_status: movie.viewing_status,
        is_favorite: movie.is_favorite,
      });
    } else {
      setMovieData({});
    }
  }, [movie]);

  const handleChange = (field: keyof MovieUpdate) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { value: any } }
  ) => {
    const value = event.target.value;
    
    // Handle numeric fields
    if (field === 'release_year' || field === 'runtime') {
      setMovieData(prev => ({
        ...prev,
        [field]: value ? parseInt(value, 10) : undefined,
      }));
    } else {
      setMovieData(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handleSubmit = async () => {
    // Basic validation
    if (movieData.title !== undefined && !movieData.title.trim()) {
      setError('Movie title cannot be empty');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const success = await onSave(movieData);
      if (success) {
        onClose();
      } else {
        setError('Failed to update movie. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const currentYear = new Date().getFullYear();

  if (!movie) {
    return null;
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <MovieIcon color="primary" />
        Edit Movie
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <TextField
            label="Title"
            value={movieData.title || ''}
            onChange={handleChange('title')}
            fullWidth
            required
          />

          <TextField
            label="Director"
            value={movieData.director || ''}
            onChange={handleChange('director')}
            fullWidth
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Release Year"
              type="number"
              value={movieData.release_year || ''}
              onChange={handleChange('release_year')}
              fullWidth
              inputProps={{ min: 1900, max: currentYear + 5 }}
            />

            <TextField
              label="Runtime (minutes)"
              type="number"
              value={movieData.runtime || ''}
              onChange={handleChange('runtime')}
              fullWidth
              inputProps={{ min: 0 }}
            />
          </Box>

          <TextField
            label="Genre"
            value={movieData.genre || ''}
            onChange={handleChange('genre')}
            fullWidth
            placeholder="e.g., Action, Drama, Comedy"
          />

          <TextField
            label="Description"
            value={movieData.description || ''}
            onChange={handleChange('description')}
            fullWidth
            multiline
            rows={3}
          />

          <TextField
            label="Poster Image URL"
            value={movieData.poster_image_url || ''}
            onChange={handleChange('poster_image_url')}
            fullWidth
            placeholder="https://example.com/poster.jpg"
          />

          <FormControl fullWidth>
            <InputLabel>Viewing Status</InputLabel>
            <Select
              value={movieData.viewing_status || ''}
              label="Viewing Status"
              onChange={(e) => handleChange('viewing_status')(e as any)}
            >
              <MenuItem value="want_to_watch">Want to Watch</MenuItem>
              <MenuItem value="watched">Watched</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EditMovieDialog;