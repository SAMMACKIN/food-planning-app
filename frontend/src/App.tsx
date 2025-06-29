import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import { ThemeProvider } from './contexts/ThemeContext';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/Loading/LoadingSpinner';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import FamilyManagement from './pages/Family/FamilyManagement';
import PantryManagement from './pages/Pantry/PantryManagement';
import MealRecommendations from './pages/Recommendations/MealRecommendations';
import MealPlanning from './pages/MealPlanning/MealPlanning';
import UserGuide from './pages/UserGuide/UserGuide';
import Changes from './pages/Changes/Changes';
import AdminDashboard from './pages/Admin/AdminDashboard';
import SavedRecipes from './pages/Recipes/SavedRecipes';
import './App.css';


// Debug component to show which backend we're pointing to
const BackendDebugBanner = () => {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  const isProduction = apiUrl.includes('production');
  const isPreview = apiUrl.includes('preview');
  const isLocal = apiUrl.includes('localhost');
  
  let environment = 'Unknown';
  
  if (isProduction) {
    environment = 'Production';
  } else if (isPreview) {
    environment = 'Preview';
  } else if (isLocal) {
    environment = 'Local';
  }
  
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        backgroundColor: isProduction ? '#4caf50' : isPreview ? '#ff9800' : '#2196f3',
        color: 'white',
        padding: '4px 8px',
        textAlign: 'center',
        fontSize: '12px',
        fontFamily: 'monospace',
        borderBottom: '1px solid rgba(255,255,255,0.3)'
      }}
    >
      <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '11px' }}>
        Backend: <strong>{environment}</strong> ({apiUrl})
      </Typography>
    </Box>
  );
};

function App() {
  const { isAuthenticated, isLoading, checkAuth, user } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <ThemeProvider>
        <LoadingSpinner 
          fullPage 
          message="Setting up your food planning experience..." 
        />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <BackendDebugBanner />
      <Box sx={{ paddingTop: '24px' }}>
        <Router>
        <Routes>
          <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
          <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
          <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="family" element={<FamilyManagement />} />
            <Route path="pantry" element={<PantryManagement />} />
            <Route path="recommendations" element={<MealRecommendations />} />
            <Route path="recipes" element={<SavedRecipes />} />
            <Route path="meal-planning" element={<MealPlanning />} />
            <Route path="user-guide" element={<UserGuide />} />
            <Route path="changes" element={<Changes />} />
            <Route path="admin" element={
              isAuthenticated && user?.is_admin ? 
                <AdminDashboard /> : 
                <Navigate to="/dashboard" />
            } />
          </Route>
        </Routes>
      </Router>
      </Box>
    </ThemeProvider>
  );
}

export default App;
