import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Box, Typography, Paper } from '@mui/material';

const NavigationDebug: React.FC = () => {
  const location = useLocation();

  useEffect(() => {
    console.log('🔄 Route changed to:', location.pathname);
  }, [location]);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Paper 
      sx={{ 
        position: 'fixed', 
        bottom: 80, 
        right: 20, 
        p: 2,
        zIndex: 1300,
        opacity: 0.9
      }}
    >
      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
        Current Route: {location.pathname}
      </Typography>
    </Paper>
  );
};

export default NavigationDebug;