import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Container,
  Alert,
  Button,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Tv as TVIcon,
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Star as StarIcon,
} from '@mui/icons-material';

const TVShowsManagement: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TVIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
            <Typography variant="h4" component="h1" fontWeight="bold">
              My TV Shows
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Track your favorite shows, discover new series, and get personalized recommendations.
          </Typography>
        </Box>

        {/* Coming Soon Alert */}
        <Alert 
          severity="info" 
          sx={{ mb: 4 }}
          icon={<TVIcon />}
        >
          <Typography variant="h6" gutterBottom>
            TV Shows Feature Coming Soon!
          </Typography>
          <Typography>
            We're building an amazing TV shows management system that will let you:
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0 }}>
            <li>Track shows you're watching, want to watch, and have completed</li>
            <li>Monitor your progress through seasons and episodes</li>
            <li>Rate and review your favorite series</li>
            <li>Get AI-powered show recommendations based on your taste</li>
            <li>Share your watchlist with friends</li>
            <li>Discover trending and popular shows</li>
          </Box>
        </Alert>

        {/* Feature Preview Cards */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PlayIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    Watch Progress Tracking
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Keep track of which episodes you've watched, automatically update your progress, 
                  and never lose your place in a series again.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <StarIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    Smart Recommendations
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Get personalized show recommendations powered by AI based on your viewing history, 
                  ratings, and favorite genres.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AddIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    Watchlist Management
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Organize shows into custom lists like "Want to Watch", "Currently Watching", 
                  and "Completed" with sorting and filtering options.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TVIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    Show Discovery
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Discover new shows through integration with external APIs, trending lists, 
                  and recommendations from other users in the community.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Call to Action */}
        <Paper sx={{ p: 4, mt: 4, textAlign: 'center', bgcolor: 'background.default' }}>
          <Typography variant="h6" gutterBottom>
            Stay Tuned!
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            The TV Shows feature is currently under development. We'll notify you as soon as it's ready!
          </Typography>
          <Button 
            variant="outlined" 
            size="large"
            startIcon={<TVIcon />}
            disabled
          >
            Add Your First Show (Coming Soon)
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default TVShowsManagement;