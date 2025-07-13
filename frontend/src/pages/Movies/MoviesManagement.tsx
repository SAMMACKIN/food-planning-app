import React from 'react';
import { Box, Typography, Container, Alert } from '@mui/material';
import { Movie as MovieIcon } from '@mui/icons-material';

const MoviesManagement: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <MovieIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            Movies
          </Typography>
        </Box>
        
        <Alert severity="info">
          Movies feature coming soon! Build your collection, track what you've watched, and discover new films.
        </Alert>
      </Box>
    </Container>
  );
};

export default MoviesManagement;