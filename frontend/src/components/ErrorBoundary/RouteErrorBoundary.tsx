import React from 'react';
import { useLocation } from 'react-router-dom';
import ErrorBoundary from './ErrorBoundary';
import { Box, Typography, Button } from '@mui/material';
import { Home } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface RouteErrorBoundaryProps {
  children: React.ReactNode;
}

const RouteErrorFallback: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ textAlign: 'center', p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Error loading {location.pathname}
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        There was a problem loading this page. You can try refreshing or go back to the dashboard.
      </Typography>
      <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant="outlined"
          onClick={() => window.location.reload()}
        >
          Refresh Page
        </Button>
        <Button
          variant="contained"
          startIcon={<Home />}
          onClick={() => navigate('/dashboard')}
        >
          Go to Dashboard
        </Button>
      </Box>
    </Box>
  );
};

const RouteErrorBoundary: React.FC<RouteErrorBoundaryProps> = ({ children }) => {
  const location = useLocation();

  // Reset error boundary when route changes
  const key = location.pathname;

  return (
    <ErrorBoundary
      key={key}
      fallback={<RouteErrorFallback />}
      onError={(error, errorInfo) => {
        console.error(`Route error on ${location.pathname}:`, error);
      }}
    >
      {children}
    </ErrorBoundary>
  );
};

export default RouteErrorBoundary;