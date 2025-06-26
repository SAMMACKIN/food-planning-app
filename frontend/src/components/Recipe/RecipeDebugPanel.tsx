import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  ExpandMore,
  BugReport,
  Visibility,
  VisibilityOff,
  Refresh,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';

interface RecipeDebugPanelProps {
  error?: string | null;
  onClearError?: () => void;
}

const RecipeDebugPanel: React.FC<RecipeDebugPanelProps> = ({ error, onClearError }) => {
  const [expanded, setExpanded] = useState(false);
  const [testResults, setTestResults] = useState<any[]>([]);

  const runDiagnostics = async () => {
    const results: any[] = [];
    
    try {
      // Test 1: Check authentication
      const token = localStorage.getItem('access_token');
      results.push({
        test: 'Authentication Token',
        status: token ? 'success' : 'error',
        message: token ? `Token exists (${token.length} chars)` : 'No token found',
        action: token ? null : 'Please log in again'
      });

      if (!token) {
        setTestResults(results);
        return;
      }

      // Test 2: Check API connectivity
      try {
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
        const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const user = await response.json();
          results.push({
            test: 'API Connectivity',
            status: 'success',
            message: `Connected as ${user.email}`,
            action: null
          });

          // Test 3: Check backend health
          const statusResponse = await fetch(`${apiUrl}/api/v1/recommendations/status`);
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            results.push({
              test: 'Backend Health',
              status: 'success',
              message: `Available providers: ${status.available_providers.join(', ')}`,
              action: null
            });
          } else {
            results.push({
              test: 'Backend Health',
              status: 'warning',
              message: 'Recommendations service may be down',
              action: 'Check backend logs'
            });
          }

        } else {
          results.push({
            test: 'API Connectivity',
            status: 'error',
            message: `Authentication failed (${response.status})`,
            action: 'Please log out and log in again'
          });
        }
      } catch (networkError: any) {
        results.push({
          test: 'API Connectivity',
          status: 'error',
          message: 'Cannot connect to backend server',
          action: 'Check if backend is running on port 8001'
        });
      }

      // Test 4: Check recipe system health
      if (results.some(r => r.test === 'API Connectivity' && r.status === 'success')) {
        try {
          const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
          const healthResponse = await fetch(`${apiUrl}/api/v1/recipes/debug/health`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            if (healthData.status === 'healthy') {
              const tableInfo = Object.entries(healthData.tables || {})
                .map(([name, info]: [string, any]) => `${name}(${info.exists ? info.count : 'missing'})`)
                .join(', ');
              
              results.push({
                test: 'Recipe System Health',
                status: 'success',
                message: `All systems operational. Tables: ${tableInfo}`,
                action: null
              });
            } else {
              results.push({
                test: 'Recipe System Health',
                status: 'error',
                message: `Health check failed: ${healthData.error || 'Unknown error'}`,
                action: 'Check backend logs for details'
              });
            }
          } else {
            results.push({
              test: 'Recipe System Health',
              status: 'error',
              message: `Health endpoint failed (${healthResponse.status})`,
              action: 'Check if backend is properly configured'
            });
          }
        } catch (healthError) {
          results.push({
            test: 'Recipe System Health',
            status: 'error',
            message: 'Health check request failed',
            action: 'Check network connectivity and backend status'
          });
        }
      }

      // Test 5: Check basic recipe database access
      if (results.some(r => r.test === 'API Connectivity' && r.status === 'success')) {
        try {
          const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
          const recipesResponse = await fetch(`${apiUrl}/api/v1/recipes`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (recipesResponse.ok) {
            const recipes = await recipesResponse.json();
            results.push({
              test: 'Recipe Database Access',
              status: 'success',
              message: `Retrieved ${recipes.length} saved recipes`,
              action: null
            });
          } else {
            results.push({
              test: 'Recipe Database Access',
              status: 'error',
              message: `Recipe API failed (${recipesResponse.status})`,
              action: 'Check database schema and user permissions'
            });
          }
        } catch (dbError) {
          results.push({
            test: 'Recipe Database Access',
            status: 'error',
            message: 'Recipe database query failed',
            action: 'Check database connection and schema'
          });
        }
      }

    } catch (error: any) {
      results.push({
        test: 'Diagnostic Runner',
        status: 'error',
        message: `Unexpected error: ${error.message}`,
        action: 'Check browser console for details'
      });
    }

    setTestResults(results);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle color="success" />;
      case 'warning': return <Warning color="warning" />;
      case 'error': return <Error color="error" />;
      default: return <BugReport />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card sx={{ mt: 2, border: '2px dashed', borderColor: 'warning.main' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <BugReport color="warning" />
            <Typography variant="h6">Recipe Debug Panel</Typography>
            <Chip label="Development Tool" size="small" color="warning" />
          </Box>
          <IconButton onClick={() => setExpanded(!expanded)}>
            {expanded ? <VisibilityOff /> : <Visibility />}
          </IconButton>
        </Box>

        <Collapse in={expanded}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={onClearError}>
              <Typography variant="subtitle2">Current Error:</Typography>
              {error}
            </Alert>
          )}

          <Box mb={2}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={runDiagnostics}
              size="small"
            >
              Run Diagnostics
            </Button>
          </Box>

          {testResults.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Diagnostic Results:
              </Typography>
              <List dense>
                {testResults.map((result, index) => (
                  <ListItem key={index}>
                    <Box display="flex" alignItems="center" width="100%" gap={1}>
                      {getStatusIcon(result.status)}
                      <ListItemText
                        primary={result.test}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {result.message}
                            </Typography>
                            {result.action && (
                              <Chip 
                                label={`Action: ${result.action}`} 
                                size="small" 
                                color={getStatusColor(result.status) as any}
                                variant="outlined"
                                sx={{ mt: 0.5 }}
                              />
                            )}
                          </Box>
                        }
                      />
                    </Box>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle2">Manual Testing Instructions</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" paragraph>
                If you're still experiencing issues, try these steps:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="1. Open Browser Console (F12)"
                    secondary="Look for error messages when saving recipes"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="2. Check Network Tab"
                    secondary="Look for failed API requests (red status codes)"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="3. Try Logout/Login"
                    secondary="Authentication tokens may have expired"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="4. Check Backend Server"
                    secondary="Ensure backend is running on http://localhost:8001"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default RecipeDebugPanel;