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
  Movie as MovieIcon,
  Add as AddIcon,
  LocalMovies as FilmIcon,
  Star as StarIcon,
  Search as SearchIcon,
} from '@mui/icons-material';

const MoviesManagement: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <MovieIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
            <Typography variant="h4" component="h1" fontWeight="bold">
              My Movies
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Build your movie collection, discover new films, and get personalized recommendations.
          </Typography>
        </Box>

        {/* Coming Soon Alert */}
        <Alert 
          severity="info" 
          sx={{ mb: 4 }}
          icon={<FilmIcon />}
        >
          <Typography variant="h6" gutterBottom>
            Movies Feature Coming Soon!
          </Typography>
          <Typography>
            We're creating a comprehensive movie management system that will allow you to:
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0 }}>
            <li>Maintain watchlists for movies you want to see and have watched</li>
            <li>Rate and review films with detailed feedback</li>
            <li>Get intelligent movie recommendations based on your preferences</li>
            <li>Organize movies by genre, decade, director, and custom tags</li>
            <li>Share movie recommendations with friends</li>
            <li>Track your movie watching statistics and trends</li>
          </Box>
        </Alert>

        {/* Feature Preview Cards */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SearchIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    Movie Discovery
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Search through vast movie databases, explore by genre, director, or year, 
                  and discover hidden gems tailored to your taste.
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
                    Rating & Reviews
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Rate movies on a 5-star scale, write detailed reviews, and track your 
                  movie preferences over time with comprehensive analytics.
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
                    Custom Collections
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Create custom movie lists like "Weekend Classics", "Date Night Movies", 
                  or "Sci-Fi Favorites" and organize your collection your way.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <FilmIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6" fontWeight="medium">
                    AI Recommendations
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Get personalized movie suggestions powered by AI that learns from your 
                  viewing history, ratings, and favorite genres and directors.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Statistics Preview */}
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Future Analytics Dashboard
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main" fontWeight="bold">
                      ---
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Movies Watched
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main" fontWeight="bold">
                      ---
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Hours Watched
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main" fontWeight="bold">
                      ---
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Rating
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main" fontWeight="bold">
                      ---
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Favorite Genre
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>

        {/* Call to Action */}
        <Paper sx={{ p: 4, mt: 4, textAlign: 'center', bgcolor: 'background.default' }}>
          <Typography variant="h6" gutterBottom>
            Coming to Theaters Soon! 🎬
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            The Movies feature is in active development. Get ready to build your ultimate movie collection!
          </Typography>
          <Button 
            variant="outlined" 
            size="large"
            startIcon={<MovieIcon />}
            disabled
          >
            Add Your First Movie (Coming Soon)
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default MoviesManagement;