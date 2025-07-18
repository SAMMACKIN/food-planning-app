import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Skeleton,
} from '@mui/material';
import {
  AutoAwesome as RecommendationsIcon,
  Movie as MovieIcon,
  Tv as TvIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  ArrowBack as BackIcon,
  Star as StarIcon,
  Category as GenreIcon,
  Person as DirectorIcon,
  CalendarToday as YearIcon,
} from '@mui/icons-material';
import { MovieCreate } from '../../types';
import { moviesApi } from '../../services/moviesApi';

interface Recommendation {
  title: string;
  year: number;
  genre: string;
  director: string;
  description: string;
  why_recommended: string;
  content_type: 'movie' | 'tv_show';
}

const MovieRecommendations: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [contentType, setContentType] = useState<'all' | 'movie' | 'tv'>('all');
  const [genre, setGenre] = useState('');
  const [provider, setProvider] = useState<string>('');
  const [addingMovieId, setAddingMovieId] = useState<string | null>(null);

  const commonGenres = [
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary',
    'Drama', 'Family', 'Fantasy', 'Horror', 'Mystery', 'Romance',
    'Sci-Fi', 'Thriller', 'War', 'Western'
  ];

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/v1/movies/recommendations?` +
        new URLSearchParams({
          ...(contentType !== 'all' && { content_type: contentType }),
          ...(genre && { genre }),
          limit: '10'
        }),
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get recommendations');
      }

      const data = await response.json();
      
      if (data.success) {
        setRecommendations(data.recommendations || []);
        setProvider(data.provider || '');
      } else {
        setError(data.error || 'Failed to get recommendations');
      }
    } catch (err: any) {
      console.error('Error loading recommendations:', err);
      setError('Failed to load recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [contentType, genre]);

  const handleAddToCollection = async (recommendation: Recommendation) => {
    try {
      setAddingMovieId(recommendation.title);
      
      const movieData: MovieCreate = {
        title: recommendation.title,
        genre: recommendation.genre,
        director: recommendation.director,
        release_year: recommendation.year,
        description: recommendation.description,
        viewing_status: 'want_to_watch',
        source: 'ai_recommendation'
      };

      await moviesApi.createMovie(movieData);
      
      // Show success briefly
      setRecommendations(prev => 
        prev.map(rec => 
          rec.title === recommendation.title 
            ? { ...rec, added: true } as any
            : rec
        )
      );
    } catch (err: any) {
      console.error('Error adding to collection:', err);
      setError('Failed to add to collection');
    } finally {
      setAddingMovieId(null);
    }
  };

  const renderRecommendationCard = (recommendation: Recommendation, index: number) => {
    const isAdding = addingMovieId === recommendation.title;
    const isAdded = (recommendation as any).added;
    
    return (
      <Grid item xs={12} md={6} key={`${recommendation.title}-${index}`}>
        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ flexGrow: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6" component="h3" gutterBottom>
                  {recommendation.title}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                  <Chip
                    label={recommendation.content_type === 'tv_show' ? 'TV Show' : 'Movie'}
                    icon={recommendation.content_type === 'tv_show' ? <TvIcon /> : <MovieIcon />}
                    size="small"
                    color={recommendation.content_type === 'tv_show' ? 'secondary' : 'primary'}
                  />
                  {recommendation.year && (
                    <Chip
                      label={recommendation.year}
                      icon={<YearIcon />}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {recommendation.genre && (
                    <Chip
                      label={recommendation.genre}
                      icon={<GenreIcon />}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
                {recommendation.director && (
                  <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <DirectorIcon sx={{ fontSize: 16 }} />
                    {recommendation.director}
                  </Typography>
                )}
              </Box>
            </Box>

            <Typography variant="body2" paragraph>
              {recommendation.description}
            </Typography>

            <Paper sx={{ p: 2, bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <StarIcon sx={{ color: 'primary.main', fontSize: 20 }} />
                <Typography variant="subtitle2" color="primary.main">
                  Why we recommend this
                </Typography>
              </Box>
              <Typography variant="body2">
                {recommendation.why_recommended}
              </Typography>
            </Paper>
          </CardContent>
          
          <CardActions>
            <Button
              size="small"
              variant="contained"
              startIcon={isAdding ? <CircularProgress size={16} /> : isAdded ? null : <AddIcon />}
              onClick={() => handleAddToCollection(recommendation)}
              disabled={isAdding || isAdded}
              sx={{ ml: 'auto' }}
            >
              {isAdded ? 'Added!' : 'Add to Collection'}
            </Button>
          </CardActions>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton onClick={() => navigate('/movies')}>
            <BackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <RecommendationsIcon color="primary" />
            Recommendations
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={contentType}
              label="Type"
              onChange={(e) => setContentType(e.target.value as any)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="movie">Movies</MenuItem>
              <MenuItem value="tv">TV Shows</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Genre</InputLabel>
            <Select
              value={genre}
              label="Genre"
              onChange={(e) => setGenre(e.target.value)}
            >
              <MenuItem value="">Any Genre</MenuItem>
              {commonGenres.map(g => (
                <MenuItem key={g} value={g}>{g}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Tooltip title="Get new recommendations">
            <IconButton 
              onClick={loadRecommendations}
              disabled={loading}
              color="primary"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Provider info */}
      {provider && !loading && recommendations.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Recommendations powered by {provider === 'claude' ? 'Claude AI' : provider === 'perplexity' ? 'Perplexity AI' : 'AI'}
        </Alert>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} md={6} key={i}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
                  <Skeleton variant="rectangular" height={60} sx={{ mt: 2 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Recommendations */}
      {!loading && recommendations.length > 0 && (
        <Grid container spacing={3}>
          {recommendations.map((rec, index) => renderRecommendationCard(rec, index))}
        </Grid>
      )}

      {/* Empty state */}
      {!loading && recommendations.length === 0 && !error && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <RecommendationsIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No recommendations available
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Add more movies and TV shows to your collection to get personalized recommendations.
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/movies')}
          >
            Go to Collection
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default MovieRecommendations;