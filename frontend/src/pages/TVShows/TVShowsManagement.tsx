import React from 'react';
import { Box, Typography, Container, Alert } from '@mui/material';
import { Tv as TVIcon } from '@mui/icons-material';

const TVShowsManagement: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <TVIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            TV Shows
          </Typography>
        </Box>
        
        <Alert severity="info">
          TV Shows feature coming soon! Track your favorite shows, monitor progress, and get recommendations.
        </Alert>
      </Box>
    </Container>
  );
};

export default TVShowsManagement;