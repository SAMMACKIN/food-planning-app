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
    'Biography', 'History', 'Self-Help', 'Business', 'Psychology', 'Philosophy',
    'Science', 'Technology', 'Health', 'Cooking', 'Travel', 'Art', 'Poetry'
  ];

  // Load recommendations on component mount
  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: RecommendationRequest = {
        max_recommendations: maxRecommendations,
        exclude_genres: excludeGenres,
        preferred_genres: preferredGenres,
        include_reasoning: includeReasoning
      };

      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/books/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP ${response.status}`);
      }

      const data: RecommendationsResponse = await response.json();
      setRecommendations(data.recommendations);
      setSessionId(data.session_id);
      setContextSummary(data.context_summary);
      
    } catch (error: any) {
      console.error('Error loading recommendations:', error);
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
      <Card key={`${recommendation.title}_${index}`} sx={{ height: 'fit-content' }}>
        {/* Book cover and title area */}
        <Box
          sx={{
            height: 120,
            bgcolor: 'grey.100',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            backgroundImage: recommendation.cover_image_url ? `url(${recommendation.cover_image_url})` : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
          {!recommendation.cover_image_url && <BookIcon sx={{ fontSize: 48, color: 'grey.500' }} />}
          
          {/* Confidence indicator */}
          {recommendation.confidence_score && (
            <Chip
              size="small"
              label={`${Math.round(recommendation.confidence_score * 100)}% match`}
              sx={{ 
                position: 'absolute', 
                top: 8, 
                right: 8,
                bgcolor: 'rgba(255,255,255,0.9)',
                color: recommendation.confidence_score > 0.8 ? 'success.main' : 
                       recommendation.confidence_score > 0.6 ? 'warning.main' : 'error.main'
              }}
            />
          )}
        </Box>
        
        <CardContent sx={{ pb: 1 }}>
          <Typography variant="h6" component="h3" noWrap title={recommendation.title}>
            {recommendation.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap title={recommendation.author}>
            by {recommendation.author}
          </Typography>
          
          {recommendation.genre && (
            <Chip
              label={recommendation.genre}
              size="small"
              sx={{ mt: 1, fontSize: '0.75rem' }}
            />
          )}
          
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {recommendation.publication_year && (
              <Chip size="small" label={recommendation.publication_year} variant="outlined" />
            )}
            {recommendation.pages && (
              <Chip size="small" label={`${recommendation.pages} pages`} variant="outlined" />
            )}
          </Box>
          
          {/* Description */}
          {recommendation.description && (
            <Typography 
              variant="body2" 
              color="text.secondary" 
              sx={{ 
                mt: 1,
                display: '-webkit-box',
                WebkitLineClamp: isExpanded ? 'none' : 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}
            >
              {recommendation.description}
            </Typography>
          )}
          
          {/* AI Reasoning - Collapsible */}
          {recommendation.reasoning && (
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Box sx={{ mt: 2, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
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
            </Collapse>
          )}
        </CardContent>
        
        <CardActions sx={{ pt: 0, px: 2, pb: 2, flexDirection: 'column', gap: 1 }}>
          {/* Expand/Collapse button */}
          {(recommendation.description || recommendation.reasoning) && (
            <Button
              size="small"
              onClick={() => toggleExpanded(index)}
              startIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ alignSelf: 'stretch' }}
            >
              {isExpanded ? 'Show Less' : 'Show More'}
            </Button>
          )}
          
          <Divider sx={{ width: '100%' }} />
          
          {/* Feedback buttons */}
          <Box sx={{ display: 'flex', gap: 1, width: '100%', flexWrap: 'wrap' }}>
            <Button
              size="small"
              color="success"
              startIcon={<CheckIcon />}
              onClick={() => handleFeedback(recommendation, 'read')}
              disabled={isProcessingFeedback}
              sx={{ flex: 1, minWidth: 'fit-content' }}
            >
              {feedbackLoading === `${recommendation.title}_read` ? <CircularProgress size={16} /> : 'Read'}
            </Button>
            
            <Button
              size="small"
              color="primary"
              startIcon={<WantToReadIcon />}
              onClick={() => handleFeedback(recommendation, 'want_to_read')}
              disabled={isProcessingFeedback}
              sx={{ flex: 1, minWidth: 'fit-content' }}
            >
              {feedbackLoading === `${recommendation.title}_want_to_read` ? <CircularProgress size={16} /> : 'Want to Read'}
            </Button>
            
            <Button
              size="small"
              color="error"
              startIcon={<NotInterestedIcon />}
              onClick={() => handleFeedback(recommendation, 'not_interested')}
              disabled={isProcessingFeedback}
              sx={{ flex: 1, minWidth: 'fit-content' }}
            >
              {feedbackLoading === `${recommendation.title}_not_interested` ? <CircularProgress size={16} /> : 'Not Interested'}
            </Button>
          </Box>
        </CardActions>
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
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {recommendations.map((recommendation, index) => (
            <Box 
              key={`${recommendation.title}_${index}`}
              sx={{ 
                flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)' },
                minWidth: 0
              }}
            >
              {renderRecommendationCard(recommendation, index)}
            </Box>
          ))}
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