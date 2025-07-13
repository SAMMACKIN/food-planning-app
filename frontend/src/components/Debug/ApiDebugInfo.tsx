import React from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { useAuthStore } from '../../store/authStore';

const ApiDebugInfo: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const token = localStorage.getItem('access_token');
  
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  const environment = process.env.NODE_ENV;
  const isProduction = window.location.hostname.includes('vercel.app');
  const isPreview = window.location.hostname.includes('preview');
  
  return (
    <Paper sx={{ p: 2, m: 2, backgroundColor: 'grey.100' }}>
      <Typography variant="h6" gutterBottom>
        🔧 API Debug Information
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Typography variant="body2">
          <strong>Environment:</strong> {environment}
        </Typography>
        
        <Typography variant="body2">
          <strong>API URL:</strong> {apiUrl}
        </Typography>
        
        <Typography variant="body2">
          <strong>Current Host:</strong> {window.location.hostname}
        </Typography>
        
        <Typography variant="body2">
          <strong>Is Production:</strong> {isProduction ? 'Yes' : 'No'}
        </Typography>
        
        <Typography variant="body2">
          <strong>Is Preview:</strong> {isPreview ? 'Yes' : 'No'}
        </Typography>
        
        <Typography variant="body2">
          <strong>Authenticated:</strong> {isAuthenticated ? 'Yes' : 'No'}
        </Typography>
        
        <Typography variant="body2">
          <strong>User ID:</strong> {user?.id || 'Not logged in'}
        </Typography>
        
        <Typography variant="body2">
          <strong>Token Available:</strong> {token ? `Yes (${token.length} chars)` : 'No'}
        </Typography>
        
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" gutterBottom>
            <strong>Expected Backend URLs:</strong>
          </Typography>
          {isPreview && (
            <Chip 
              label="Preview: https://food-planning-app-preview.up.railway.app" 
              size="small" 
              color="primary" 
            />
          )}
          {isProduction && !isPreview && (
            <Chip 
              label="Production: https://food-planning-app-production.up.railway.app" 
              size="small" 
              color="success" 
            />
          )}
          {!isProduction && (
            <Chip 
              label="Local: http://localhost:8001" 
              size="small" 
              color="default" 
            />
          )}
        </Box>
      </Box>
    </Paper>
  );
};

export default ApiDebugInfo;