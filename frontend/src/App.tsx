import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout/Layout';
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
import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
    },
    secondary: {
      main: '#ff6f00',
    },
  },
});

function App() {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
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
            <Route path="meal-planning" element={<MealPlanning />} />
            <Route path="user-guide" element={<UserGuide />} />
            <Route path="changes" element={<Changes />} />
            <Route path="admin" element={
              isAuthenticated && useAuthStore.getState().user?.is_admin ? 
                <AdminDashboard /> : 
                <Navigate to="/dashboard" />
            } />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
