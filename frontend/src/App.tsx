import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
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
import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
      light: '#60ad5e',
      dark: '#005005',
    },
    secondary: {
      main: '#ff6f00',
      light: '#ffa040',
      dark: '#c43e00',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    grey: {
      50: '#f8f9fa',
      100: '#f1f3f4',
      200: '#e8eaed',
    },
  },
  typography: {
    // Mobile-first typography
    h1: {
      fontSize: '1.75rem',
      fontWeight: 700,
      lineHeight: 1.2,
      '@media (min-width:600px)': {
        fontSize: '2.5rem',
      },
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.3,
      '@media (min-width:600px)': {
        fontSize: '2rem',
      },
    },
    h3: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      '@media (min-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h4: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.4,
      '@media (min-width:600px)': {
        fontSize: '1.25rem',
      },
    },
    body1: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      '@media (min-width:600px)': {
        fontSize: '1rem',
      },
    },
    body2: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      '@media (min-width:600px)': {
        fontSize: '0.875rem',
      },
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
      fontSize: '0.875rem',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
  components: {
    // Mobile-optimized component defaults
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 24px',
          fontSize: '0.875rem',
          fontWeight: 500,
          minHeight: 44, // Touch target minimum
          textTransform: 'none',
          '@media (max-width:600px)': {
            padding: '14px 20px',
            fontSize: '0.875rem',
            minHeight: 48, // Larger touch target on mobile
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(46, 125, 50, 0.15)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(46, 125, 50, 0.25)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
          '&:hover': {
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
          },
          '@media (max-width:600px)': {
            borderRadius: 12,
            margin: '0 4px',
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: '20px',
          '@media (max-width:600px)': {
            padding: '16px',
          },
          '&:last-child': {
            paddingBottom: '20px',
            '@media (max-width:600px)': {
              paddingBottom: '16px',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          height: 32,
          fontSize: '0.75rem',
          '@media (max-width:600px)': {
            height: 36,
            fontSize: '0.8rem',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            '@media (max-width:600px)': {
              '& input': {
                padding: '16px 14px',
              },
            },
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          '@media (max-width:600px)': {
            margin: 16,
            width: 'calc(100% - 32px)',
            maxWidth: 'none',
            borderRadius: 12,
          },
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          '@media (max-width:600px)': {
            padding: '16px',
          },
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          '@media (max-width:600px)': {
            width: 64,
            height: 64,
          },
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          height: 70,
        },
      },
    },
    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          minWidth: 'auto',
          '&.Mui-selected': {
            paddingTop: 8,
          },
        },
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
});

function App() {
  const { isAuthenticated, isLoading, checkAuth, user } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <LoadingSpinner 
          fullPage 
          message="Setting up your food planning experience..." 
        />
      </ThemeProvider>
    );
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
              isAuthenticated && user?.is_admin ? 
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
