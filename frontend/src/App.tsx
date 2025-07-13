import React, { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import { ThemeProvider } from './contexts/ThemeContext';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/Loading/LoadingSpinner';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary';
import RouteErrorBoundary from './components/ErrorBoundary/RouteErrorBoundary';
import './App.css';

// Lazy load all route components to improve performance and isolation
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const FamilyManagement = lazy(() => import('./pages/Family/FamilyManagement'));
const PantryManagement = lazy(() => import('./pages/Pantry/PantryManagement'));
const MealRecommendations = lazy(() => import('./pages/Recommendations/MealRecommendations'));
const MealPlanning = lazy(() => import('./pages/MealPlanning/MealPlanning'));
const UserGuide = lazy(() => import('./pages/UserGuide/UserGuide'));
const Changes = lazy(() => import('./pages/Changes/Changes'));
const AdminDashboard = lazy(() => import('./pages/Admin/AdminDashboard'));
const SavedRecipes = lazy(() => import('./pages/Recipes/SavedRecipes'));
const BooksManagement = lazy(() => import('./pages/Books/BooksManagement'));


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
    <ErrorBoundary>
      <ThemeProvider>
        <BackendDebugBanner />
        <Box sx={{ paddingTop: '24px' }}>
          <Router>
        <Routes>
          <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
          <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
          <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Dashboard />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="family" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <FamilyManagement />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="pantry" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <PantryManagement />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="recommendations" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <MealRecommendations />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="recipes" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <SavedRecipes />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="books" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <BooksManagement />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="meal-planning" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <MealPlanning />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="user-guide" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <UserGuide />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="changes" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Changes />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="admin" element={
              isAuthenticated && user?.is_admin ? 
                <RouteErrorBoundary>
                  <Suspense fallback={<LoadingSpinner />}>
                    <AdminDashboard />
                  </Suspense>
                </RouteErrorBoundary> : 
                <Navigate to="/dashboard" />
            } />
          </Route>
        </Routes>
      </Router>
      </Box>
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
