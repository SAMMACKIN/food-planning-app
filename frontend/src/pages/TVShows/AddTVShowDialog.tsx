import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { TVShowCreate } from '../../types';

interface AddTVShowDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (tvShow: TVShowCreate) => Promise<boolean>;
}

const AddTVShowDialog: React.FC<AddTVShowDialogProps> = ({ open, onClose, onAdd }) => {
  const [formData, setFormData] = useState<TVShowCreate>({
    title: '',
    description: '',
    genre: '',
    network: '',
    total_seasons: undefined,
    total_episodes: undefined,
    status: '',
    first_air_date: undefined,
    last_air_date: undefined,
    poster_image_url: '',
    tmdb_id: '',
    tvmaze_id: '',
    imdb_id: '',
    viewing_status: 'want_to_watch',
    current_season: 1,
    current_episode: 1,
    user_notes: '',
    is_favorite: false,
    source: 'user_added',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof TVShowCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!formData.title) {
      setError('Title is required');
      return;
    }

    setLoading(true);
    setError(null);

    const success = await onAdd({
      ...formData,
      first_air_date: formData.first_air_date ? new Date(formData.first_air_date).toISOString() : undefined,
      last_air_date: formData.last_air_date ? new Date(formData.last_air_date).toISOString() : undefined,
    });

    setLoading(false);

    if (success) {
      onClose();
      // Reset form
      setFormData({
        title: '',
        description: '',
        genre: '',
        network: '',
        total_seasons: undefined,
        total_episodes: undefined,
        status: '',
        first_air_date: undefined,
        last_air_date: undefined,
        poster_image_url: '',
        tmdb_id: '',
        tvmaze_id: '',
        imdb_id: '',
        viewing_status: 'want_to_watch',
        current_season: 1,
        current_episode: 1,
        user_notes: '',
        is_favorite: false,
        source: 'user_added',
      });
    } else {
      setError('Failed to add TV show');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add TV Show</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                required
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={formData.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Genre"
                value={formData.genre || ''}
                onChange={(e) => handleChange('genre', e.target.value)}
                placeholder="e.g., Drama, Comedy, Sci-Fi"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Network"
                value={formData.network || ''}
                onChange={(e) => handleChange('network', e.target.value)}
                placeholder="e.g., Netflix, HBO, AMC"
              />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Total Seasons"
                type="number"
                inputProps={{ min: 1 }}
                value={formData.total_seasons || ''}
                onChange={(e) => handleChange('total_seasons', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Total Episodes"
                type="number"
                inputProps={{ min: 1 }}
                value={formData.total_episodes || ''}
                onChange={(e) => handleChange('total_episodes', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Show Status</InputLabel>
                <Select
                  value={formData.status || ''}
                  onChange={(e) => handleChange('status', e.target.value)}
                  label="Show Status"
                >
                  <MenuItem value="">Unknown</MenuItem>
                  <MenuItem value="running">Currently Running</MenuItem>
                  <MenuItem value="returning">Returning Series</MenuItem>
                  <MenuItem value="ended">Ended</MenuItem>
                  <MenuItem value="canceled">Canceled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="First Air Date"
                  value={formData.first_air_date ? new Date(formData.first_air_date) : null}
                  onChange={(newValue) => handleChange('first_air_date', newValue?.toISOString())}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Last Air Date"
                  value={formData.last_air_date ? new Date(formData.last_air_date) : null}
                  onChange={(newValue) => handleChange('last_air_date', newValue?.toISOString())}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Poster Image URL"
                value={formData.poster_image_url || ''}
                onChange={(e) => handleChange('poster_image_url', e.target.value)}
                placeholder="https://..."
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Viewing Status
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Viewing Status</InputLabel>
                <Select
                  value={formData.viewing_status}
                  onChange={(e) => handleChange('viewing_status', e.target.value)}
                  label="Viewing Status"
                >
                  <MenuItem value="want_to_watch">Want to Watch</MenuItem>
                  <MenuItem value="watching">Currently Watching</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="dropped">Dropped</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {formData.viewing_status === 'watching' && (
              <>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Current Season"
                    type="number"
                    inputProps={{ min: 1 }}
                    value={formData.current_season}
                    onChange={(e) => handleChange('current_season', parseInt(e.target.value) || 1)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Current Episode"
                    type="number"
                    inputProps={{ min: 1 }}
                    value={formData.current_episode}
                    onChange={(e) => handleChange('current_episode', parseInt(e.target.value) || 1)}
                  />
                </Grid>
              </>
            )}
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={2}
                value={formData.user_notes || ''}
                onChange={(e) => handleChange('user_notes', e.target.value)}
                placeholder="Personal notes about this show..."
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                External IDs (Optional)
              </Typography>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="TMDB ID"
                value={formData.tmdb_id || ''}
                onChange={(e) => handleChange('tmdb_id', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="TVMaze ID"
                value={formData.tvmaze_id || ''}
                onChange={(e) => handleChange('tvmaze_id', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="IMDB ID"
                value={formData.imdb_id || ''}
                onChange={(e) => handleChange('imdb_id', e.target.value)}
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={loading || !formData.title}
        >
          Add TV Show
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddTVShowDialog;