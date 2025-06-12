import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Tabs,
  Tab,
} from '@mui/material';
import { useAuthStore } from '../../store/authStore';

const Layout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const getCurrentTab = () => {
    if (location.pathname.includes('/family')) return 1;
    if (location.pathname.includes('/pantry')) return 2;
    return 0; // dashboard
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    switch (newValue) {
      case 0:
        navigate('/dashboard');
        break;
      case 1:
        navigate('/family');
        break;
      case 2:
        navigate('/pantry');
        break;
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Food Planning App
          </Typography>
          <Typography variant="body1" sx={{ mr: 2 }}>
            Welcome, {user?.name || user?.email}
          </Typography>
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={getCurrentTab()} onChange={handleTabChange} textColor="inherit" indicatorColor="secondary">
            <Tab label="Dashboard" />
            <Tab label="Family" />
            <Tab label="Pantry" />
            <Tab label="Meal Plans" disabled />
            <Tab label="Recommendations" disabled />
          </Tabs>
        </Box>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 3 }}>
        <Outlet />
      </Container>
    </Box>
  );
};

export default Layout;