import React, { useState, useEffect } from 'react';
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
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { TVShow, TVShowUpdate } from '../../types';

interface EditTVShowDialogProps {
  open: boolean;
  tvShow: TVShow;
  onClose: () => void;
  onUpdate: (updates: TVShowUpdate) => Promise<boolean>;
}

const EditTVShowDialog: React.FC<EditTVShowDialogProps> = ({ open, tvShow, onClose, onUpdate }) => {
  const [formData, setFormData] = useState<TVShowUpdate>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tvShow) {
      setFormData({
        title: tvShow.title,
        description: tvShow.description,
        genre: tvShow.genre,
        network: tvShow.network,
        total_seasons: tvShow.total_seasons,
        total_episodes: tvShow.total_episodes,
        status: tvShow.status,
        first_air_date: tvShow.first_air_date,
        last_air_date: tvShow.last_air_date,
        poster_image_url: tvShow.poster_image_url,
        viewing_status: tvShow.viewing_status,
        current_season: tvShow.current_season,
        current_episode: tvShow.current_episode,
        date_started: tvShow.date_started,
        date_finished: tvShow.date_finished,
        user_notes: tvShow.user_notes,
        is_favorite: tvShow.is_favorite,
      });
    }
  }, [tvShow]);

  const handleChange = (field: keyof TVShowUpdate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    // Clean up undefined values
    const cleanedData: TVShowUpdate = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        cleanedData[key as keyof TVShowUpdate] = value;
      }
    });

    const success = await onUpdate(cleanedData);

    setLoading(false);

    if (success) {
      onClose();
    } else {
      setError('Failed to update TV show');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit TV Show</DialogTitle>
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
                value={formData.title || ''}
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
                  value={formData.viewing_status || ''}
                  onChange={(e) => handleChange('viewing_status', e.target.value as TVShow['viewing_status'])}
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
                    value={formData.current_season || 1}
                    onChange={(e) => handleChange('current_season', parseInt(e.target.value) || 1)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Current Episode"
                    type="number"
                    inputProps={{ min: 1 }}
                    value={formData.current_episode || 1}
                    onChange={(e) => handleChange('current_episode', parseInt(e.target.value) || 1)}
                  />
                </Grid>
              </>
            )}
            
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Date Started"
                  value={formData.date_started ? new Date(formData.date_started) : null}
                  onChange={(newValue) => handleChange('date_started', newValue?.toISOString())}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Date Finished"
                  value={formData.date_finished ? new Date(formData.date_finished) : null}
                  onChange={(newValue) => handleChange('date_finished', newValue?.toISOString())}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
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
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_favorite || false}
                    onChange={(e) => handleChange('is_favorite', e.target.checked)}
                  />
                }
                label="Mark as Favorite"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Episodes Watched:</strong> {tvShow.episodes_watched} / {tvShow.total_episodes || '?'}
                  {tvShow.progress_percentage !== undefined && (
                    <> ({Math.round(tvShow.progress_percentage)}% complete)</>
                  )}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  To track individual episodes, close this dialog and use "Track Episodes" from the menu.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={loading}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EditTVShowDialog;