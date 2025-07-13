import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Paper,
  Divider,
  useTheme,
  useMediaQuery,
  Collapse,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AutoAwesome as AIIcon,
  CheckCircle as CheckIcon,
  BookmarkAdd as WantToReadIcon,
  ThumbDown as NotInterestedIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  MenuBook as BookIcon,
  Settings as SettingsIcon,
  TipsAndUpdates as TipsIcon,
} from '@mui/icons-material';

interface BookRecommendation {
  title: string;
  author: string;
  genre?: string;
  description?: string;
  publication_year?: number;
  pages?: number;
  cover_image_url?: string;
  reasoning?: string;
  confidence_score?: number;
}

interface RecommendationsResponse {
  recommendations: BookRecommendation[];
  session_id: string;
  context_summary: string;
  total_recommendations: number;
}

interface RecommendationRequest {
  max_recommendations?: number;
  exclude_genres?: string[];
  preferred_genres?: string[];
  include_reasoning?: boolean;
}

type FeedbackType = 'read' | 'want_to_read' | 'not_interested';

const BookRecommendations: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // State management
  const [recommendations, setRecommendations] = useState<BookRecommendation[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [contextSummary, setContextSummary] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState<string | null>(null);
  
  // Settings
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [maxRecommendations, setMaxRecommendations] = useState(5);
  const [excludeGenres, setExcludeGenres] = useState<string[]>([]);
  const [preferredGenres, setPreferredGenres] = useState<string[]>([]);
  const [includeReasoning, setIncludeReasoning] = useState(true);
  
  // UI state
  const [expandedRecommendations, setExpandedRecommendations] = useState<Set<number>>(new Set());
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Common genres for filtering
  const commonGenres = [
    'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Fantasy',
    'Historical Fiction', 'Biography', 'History', 'Self-Help', 'Business', 'Psychology', 
    'Philosophy', 'Science', 'Technology', 'Health', 'Cooking', 'Travel', 'Art', 'Poetry'
  ];

  // Load recommendations on component mount
  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      console.log('🚀 Starting to load book recommendations...');
      setLoading(true);
      setError(null);
      
      const request: RecommendationRequest = {
        max_recommendations: maxRecommendations,
        exclude_genres: excludeGenres,
        preferred_genres: preferredGenres,
        include_reasoning: includeReasoning
      };
      
      console.log('📋 Request params:', request);
      const url = `${process.env.REACT_APP_API_URL}/api/v1/books/recommendations`;
      console.log('🔗 Making request to:', url);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(request)
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('❌ Error response:', errorData);
        throw new Error(errorData?.detail || `HTTP ${response.status}`);
      }

      const data: RecommendationsResponse = await response.json();
      console.log('✅ Recommendations received:', data);
      
      setRecommendations(data.recommendations);
      setSessionId(data.session_id);
      setContextSummary(data.context_summary);
      
    } catch (error: any) {
      console.error('❌ Error loading recommendations:', error);
      setError(error.message || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (recommendation: BookRecommendation, feedbackType: FeedbackType) => {
    try {
      setFeedbackLoading(`${recommendation.title}_${feedbackType}`);
      
      const feedbackRequest = {
        session_id: sessionId,
        recommendation_title: recommendation.title,
        recommendation_author: recommendation.author,
        feedback_type: feedbackType
      };

      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/books/recommendations/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(feedbackRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      
      // Show success message
      let message = '';
      switch (feedbackType) {
        case 'read':
          message = `Marked "${recommendation.title}" as already read`;
          break;
        case 'want_to_read':
          message = `Added "${recommendation.title}" to your want-to-read list`;
          break;
        case 'not_interested':
          message = `Noted that you're not interested in "${recommendation.title}"`;
          break;
      }
      setSuccessMessage(message);
      
      // Remove the recommendation from the list after feedback
      setRecommendations(prev => prev.filter(rec => rec.title !== recommendation.title));
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
      
      // If we have updated recommendations, replace current ones
      if (result.updated_recommendations) {
        setRecommendations(result.updated_recommendations.recommendations);
        setSessionId(result.updated_recommendations.session_id);
        setContextSummary(result.updated_recommendations.context_summary);
      }
      
    } catch (error: any) {
      console.error('Error submitting feedback:', error);
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setFeedbackLoading(null);
    }
  };

  const handleRegenerateRecommendations = async () => {
    await loadRecommendations();
  };

  const toggleExpanded = (index: number) => {
    setExpandedRecommendations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const renderRecommendationCard = (recommendation: BookRecommendation, index: number) => {
    const isExpanded = expandedRecommendations.has(index);
    const isProcessingFeedback = feedbackLoading?.startsWith(recommendation.title);

    return (
      <Card 
        key={`${recommendation.title}_${index}`} 
        sx={{ 
          height: 'fit-content',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: 3
          }
        }}
      >
        {/* Minimal view - just title */}
        <CardContent 
          sx={{ 
            py: 1.5, 
            px: 2,
            cursor: 'pointer'
          }}
          onClick={() => toggleExpanded(index)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography 
              variant="body1" 
              component="h3" 
              sx={{ 
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                pr: 1,
                flexGrow: 1
              }}
              title={recommendation.title}
            >
              {recommendation.title}
            </Typography>
            <IconButton size="small" sx={{ ml: 1 }}>
              {isExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
            </IconButton>
          </Box>
        </CardContent>
        
        {/* Expanded details */}
        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <Divider />
          <CardContent sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              by {recommendation.author}
            </Typography>
            
            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {recommendation.genre && (
                <Chip
                  label={recommendation.genre}
                  size="small"
                  sx={{ fontSize: '0.75rem' }}
                />
              )}
              {recommendation.publication_year && (
                <Chip size="small" label={recommendation.publication_year} variant="outlined" />
              )}
              {recommendation.pages && (
                <Chip size="small" label={`${recommendation.pages} pages`} variant="outlined" />
              )}
              {recommendation.confidence_score && (
                <Chip
                  size="small"
                  label={`${Math.round(recommendation.confidence_score * 100)}% match`}
                  sx={{ 
                    color: recommendation.confidence_score > 0.8 ? 'success.main' : 
                           recommendation.confidence_score > 0.6 ? 'warning.main' : 'error.main'
                  }}
                  variant="outlined"
                />
              )}
            </Box>
            
            {/* Cover image if available */}
            {recommendation.cover_image_url && (
              <Box 
                sx={{
                  mt: 2,
                  mb: 2,
                  height: 150,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  overflow: 'hidden',
                  borderRadius: 1,
                  bgcolor: 'grey.100'
                }}
              >
                <img 
                  src={recommendation.cover_image_url} 
                  alt={recommendation.title}
                  style={{
                    maxHeight: '100%',
                    maxWidth: '100%',
                    objectFit: 'contain'
                  }}
                />
              </Box>
            )}
            
            {/* Description */}
            {recommendation.description && (
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mt: 2 }}
              >
                {recommendation.description}
              </Typography>
            )}
            
            {/* AI Reasoning */}
            {recommendation.reasoning && (
              <Box sx={{ mt: 2, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <AIIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                  <Typography variant="caption" fontWeight="bold">
                    Why we recommend this:
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {recommendation.reasoning}
                </Typography>
              </Box>
            )}
          </CardContent>
          
          <CardActions sx={{ px: 2, pb: 2, gap: 1 }}>
            <Button
              size="small"
              color="success"
              variant="outlined"
              startIcon={<CheckIcon />}
              onClick={(e) => {
                e.stopPropagation();
                handleFeedback(recommendation, 'read');
              }}
              disabled={isProcessingFeedback}
              sx={{ flex: 1 }}
            >
              {feedbackLoading === `${recommendation.title}_read` ? <CircularProgress size={16} /> : 'Read'}
            </Button>
            
            <Button
              size="small"
              color="primary"
              variant="contained"
              startIcon={<WantToReadIcon />}
              onClick={(e) => {
                e.stopPropagation();
                handleFeedback(recommendation, 'want_to_read');
              }}
              disabled={isProcessingFeedback}
              sx={{ flex: 1 }}
            >
              {feedbackLoading === `${recommendation.title}_want_to_read` ? <CircularProgress size={16} /> : 'Want'}
            </Button>
            
            <Button
              size="small"
              color="error"
              variant="outlined"
              startIcon={<NotInterestedIcon />}
              onClick={(e) => {
                e.stopPropagation();
                handleFeedback(recommendation, 'not_interested');
              }}
              disabled={isProcessingFeedback}
              sx={{ flex: 1 }}
            >
              {feedbackLoading === `${recommendation.title}_not_interested` ? <CircularProgress size={16} /> : 'Not Interested'}
            </Button>
          </CardActions>
        </Collapse>
      </Card>
    );
  };

  return (
    <Box sx={{ width: '100%', minHeight: '100vh' }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontSize: isMobile ? '1.75rem' : '2.125rem' }}>
            🤖 Book Recommendations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            AI-powered suggestions based on your reading history and preferences
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setSettingsOpen(true)}
          >
            Settings
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={handleRegenerateRecommendations}
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} /> : 'New Suggestions'}
          </Button>
        </Box>
      </Box>

      {/* Context Summary */}
      {contextSummary && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.50', border: `1px solid ${theme.palette.primary.main}` }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <TipsIcon sx={{ color: 'primary.main', mt: 0.25 }} />
            <Box>
              <Typography variant="subtitle2" color="primary.main" gutterBottom>
                How we chose these books for you:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {contextSummary}
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress />
            <Typography variant="body2" sx={{ mt: 2 }}>
              Generating personalized recommendations...
            </Typography>
          </Box>
        </Box>
      )}

      {/* Recommendations */}
      {!loading && recommendations.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {recommendations.map((recommendation, index) => renderRecommendationCard(recommendation, index))}
        </Box>
      )}

      {/* Empty State */}
      {!loading && recommendations.length === 0 && !error && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <AIIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No recommendations available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add some books to your collection first, and we'll generate personalized recommendations for you!
          </Typography>
          <Button
            variant="contained"
            onClick={handleRegenerateRecommendations}
          >
            Try Again
          </Button>
        </Box>
      )}

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Recommendation Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            <TextField
              label="Number of recommendations"
              type="number"
              value={maxRecommendations}
              onChange={(e) => setMaxRecommendations(Number(e.target.value))}
              inputProps={{ min: 1, max: 20 }}
              fullWidth
            />
            
            <TextField
              label="Preferred genres"
              select
              SelectProps={{ multiple: true }}
              value={preferredGenres}
              onChange={(e) => setPreferredGenres(Array.isArray(e.target.value) ? e.target.value : [e.target.value])}
              fullWidth
              helperText="Select genres you'd like to see more of"
            >
              {commonGenres.map((genre) => (
                <MenuItem key={genre} value={genre}>
                  {genre}
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              label="Exclude genres"
              select
              SelectProps={{ multiple: true }}
              value={excludeGenres}
              onChange={(e) => setExcludeGenres(Array.isArray(e.target.value) ? e.target.value : [e.target.value])}
              fullWidth
              helperText="Select genres you want to avoid"
            >
              {commonGenres.map((genre) => (
                <MenuItem key={genre} value={genre}>
                  {genre}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => {
              setSettingsOpen(false);
              loadRecommendations();
            }}
            variant="contained"
          >
            Apply & Refresh
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BookRecommendations;