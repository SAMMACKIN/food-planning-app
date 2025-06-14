import React, { useState } from 'react';
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
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Home as HomeIcon,
  People as PeopleIcon,
  Kitchen as KitchenIcon,
  CalendarMonth as CalendarIcon,
  Restaurant as RestaurantIcon,
  Help as HelpIcon,
  History as HistoryIcon,
  AdminPanelSettings as AdminIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../../store/authStore';

const Layout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const getCurrentTab = () => {
    if (location.pathname.includes('/family')) return 1;
    if (location.pathname.includes('/pantry')) return 2;
    if (location.pathname.includes('/meal-planning')) return 3;
    if (location.pathname.includes('/recommendations')) return 4;
    if (location.pathname.includes('/user-guide')) return 5;
    if (location.pathname.includes('/changes')) return 6;
    if (location.pathname.includes('/admin')) return 7;
    return 0; // dashboard
  };

  const getCurrentBottomNav = () => {
    if (location.pathname.includes('/family')) return 1;
    if (location.pathname.includes('/pantry')) return 2;
    if (location.pathname.includes('/meal-planning')) return 3;
    if (location.pathname.includes('/recommendations')) return 4;
    return 0; // dashboard
  };

  const navigationItems = [
    { label: 'Dashboard', icon: <HomeIcon />, path: '/dashboard' },
    { label: 'Family', icon: <PeopleIcon />, path: '/family' },
    { label: 'Pantry', icon: <KitchenIcon />, path: '/pantry' },
    { label: 'Meal Plans', icon: <CalendarIcon />, path: '/meal-planning' },
    { label: 'Recipes', icon: <RestaurantIcon />, path: '/recommendations' },
    { label: 'Help', icon: <HelpIcon />, path: '/user-guide' },
    { label: 'Changes', icon: <HistoryIcon />, path: '/changes' },
    ...(user?.is_admin ? [{ label: 'Admin', icon: <AdminIcon />, path: '/admin' }] : []),
  ];

  const primaryNavItems = navigationItems.slice(0, 5); // First 5 for bottom nav
  const secondaryNavItems = navigationItems.slice(5); // Rest for drawer

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    const item = navigationItems[newValue];
    if (item) {
      navigate(item.path);
    }
  };

  const handleBottomNavChange = (event: React.SyntheticEvent, newValue: number) => {
    const item = primaryNavItems[newValue];
    if (item) {
      navigate(item.path);
    }
  };

  const handleDrawerToggle = () => {
    setMobileDrawerOpen(!mobileDrawerOpen);
  };

  const handleDrawerNavigation = (path: string) => {
    navigate(path);
    setMobileDrawerOpen(false);
  };

  // Mobile Drawer Component
  const mobileDrawer = (
    <Box sx={{ width: 280 }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" color="primary.main" fontWeight="bold">
          🍽️ Food Planner
        </Typography>
        <IconButton onClick={handleDrawerToggle} size="small">
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />
      
      {/* User Info */}
      <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
        <Typography variant="body2" color="text.secondary">
          Welcome back!
        </Typography>
        <Typography variant="subtitle1" fontWeight="medium">
          {user?.name || user?.email}
        </Typography>
      </Box>
      
      {/* Primary Navigation */}
      <List>
        {primaryNavItems.map((item, index) => (
          <ListItemButton 
            key={item.path}
            onClick={() => handleDrawerNavigation(item.path)}
            selected={getCurrentBottomNav() === index}
            sx={{ py: 1.5 }}
          >
            <ListItemIcon sx={{ color: getCurrentBottomNav() === index ? 'primary.main' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.label} 
              primaryTypographyProps={{ 
                fontWeight: getCurrentBottomNav() === index ? 'medium' : 'normal' 
              }}
            />
          </ListItemButton>
        ))}
      </List>
      
      <Divider sx={{ my: 1 }} />
      
      {/* Secondary Navigation */}
      <List>
        {secondaryNavItems.map((item) => (
          <ListItemButton 
            key={item.path}
            onClick={() => handleDrawerNavigation(item.path)}
            sx={{ py: 1.5 }}
          >
            <ListItemIcon>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      
      <Divider sx={{ my: 1 }} />
      
      {/* Logout */}
      <List>
        <ListItemButton onClick={logout} sx={{ py: 1.5, color: 'error.main' }}>
          <ListItemIcon sx={{ color: 'error.main' }}>
            <CloseIcon />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItemButton>
      </List>
    </Box>
  );

  return (
    <Box sx={{ 
      flexGrow: 1, 
      pb: isMobile ? 7 : 0, // Add bottom padding for mobile bottom nav
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh'
    }}>
      {/* Desktop/Tablet Header */}
      <AppBar position="static" elevation={isMobile ? 0 : 1}>
        <Toolbar sx={{ minHeight: isMobile ? 56 : 64 }}>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography 
            variant={isMobile ? "h6" : "h5"} 
            component="div" 
            sx={{ 
              flexGrow: 1,
              fontWeight: 'bold',
              fontSize: isMobile ? '1.1rem' : '1.5rem'
            }}
          >
            {isMobile ? '🍽️ Food Planner' : '🍽️ Food Planning App'}
          </Typography>
          
          {!isMobile && (
            <>
              <Typography variant="body2" sx={{ mr: 2, opacity: 0.8 }}>
                Welcome, {user?.name || user?.email}
              </Typography>
              <Button 
                color="inherit" 
                onClick={logout}
                variant="outlined"
                size="small"
                sx={{ 
                  borderColor: 'rgba(255,255,255,0.3)',
                  '&:hover': { borderColor: 'rgba(255,255,255,0.7)' }
                }}
              >
                Logout
              </Button>
            </>
          )}
        </Toolbar>
        
        {/* Desktop Tabs */}
        {!isMobile && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={getCurrentTab()} 
              onChange={handleTabChange} 
              textColor="inherit" 
              indicatorColor="secondary"
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minHeight: 48 }}
            >
              {navigationItems.map((item, index) => (
                <Tab 
                  key={item.path}
                  label={item.label} 
                  icon={item.icon}
                  iconPosition="start"
                  sx={{ 
                    minHeight: 48,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    ...(item.label === 'Admin' && { color: 'error.light' })
                  }} 
                />
              ))}
            </Tabs>
          </Box>
        )}
      </AppBar>

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileDrawerOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: 280,
            },
          }}
        >
          {mobileDrawer}
        </Drawer>
      )}

      {/* Main Content */}
      <Container 
        maxWidth="lg" 
        sx={{ 
          mt: isMobile ? 1 : 3,
          px: isMobile ? 1 : 3,
          flex: 1,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Outlet />
      </Container>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <Paper 
          sx={{ 
            position: 'fixed', 
            bottom: 0, 
            left: 0, 
            right: 0,
            zIndex: 1000,
            borderTop: 1,
            borderColor: 'divider'
          }} 
          elevation={8}
        >
          <BottomNavigation
            value={getCurrentBottomNav()}
            onChange={handleBottomNavChange}
            showLabels
            sx={{
              height: 70,
              '& .MuiBottomNavigationAction-root': {
                minWidth: 'auto',
                paddingTop: 1,
                '&.Mui-selected': {
                  color: 'primary.main',
                },
              },
              '& .MuiBottomNavigationAction-label': {
                fontSize: '0.75rem',
                fontWeight: 'medium',
                '&.Mui-selected': {
                  fontSize: '0.75rem',
                },
              },
            }}
          >
            {primaryNavItems.map((item) => (
              <BottomNavigationAction
                key={item.path}
                label={item.label}
                icon={item.icon}
              />
            ))}
          </BottomNavigation>
        </Paper>
      )}
    </Box>
  );
};

export default Layout;