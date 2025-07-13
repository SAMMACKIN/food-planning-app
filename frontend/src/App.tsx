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
const TVShowsManagement = lazy(() => import('./pages/TVShows/TVShowsManagement'));
const MoviesManagement = lazy(() => import('./pages/Movies/MoviesManagement'));



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
            <Route path="tv-shows" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <TVShowsManagement />
                </Suspense>
              </RouteErrorBoundary>
            } />
            <Route path="movies" element={
              <RouteErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <MoviesManagement />
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
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
