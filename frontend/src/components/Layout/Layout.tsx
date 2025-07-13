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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Alert,
  Snackbar,
  Collapse,
} from '@mui/material';
import {
  Home as HomeIcon,
  People as PeopleIcon,
  Kitchen as KitchenIcon,
  CalendarMonth as CalendarIcon,
  AutoAwesome as RecommendationsIcon,
  MenuBook as SavedRecipesIcon,
  LocalLibrary as BooksIcon,
  Tv as TVIcon,
  Movie as MovieIcon,
  Restaurant as FoodIcon,
  Help as HelpIcon,
  History as HistoryIcon,
  AdminPanelSettings as AdminIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  DeleteForever as DeleteIcon,
  Warning as WarningIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../../store/authStore';
import { apiRequest } from '../../services/api';
import { ThemeToggle } from '../ThemeToggle';

const Layout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<{[key: string]: boolean}>({
    'Food & Recipes': true, // Food section expanded by default
    'Books': false,
    'TV Shows': false,
    'Movies': false,
    'Other': false
  });
  
  // Delete account states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [confirmationText, setConfirmationText] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  const getCurrentTab = () => {
    // Food section
    if (location.pathname.includes('/family')) return 1;
    if (location.pathname.includes('/pantry')) return 2;
    if (location.pathname.includes('/recommendations')) return 3;
    if (location.pathname.includes('/recipes')) return 4;
    if (location.pathname.includes('/meal-planning')) return 5;
    // Books section
    if (location.pathname.includes('/books/recommendations')) return 7;
    if (location.pathname.includes('/books')) return 6;
    // TV Shows section
    if (location.pathname.includes('/tv-shows')) return 8;
    // Movies section
    if (location.pathname.includes('/movies')) return 9;
    // Other sections
    if (location.pathname.includes('/user-guide')) return 10;
    if (location.pathname.includes('/changes')) return 11;
    if (location.pathname.includes('/admin')) return 12;
    return 0; // dashboard
  };

  const getCurrentBottomNav = () => {
    // Food & Recipes section
    if (location.pathname.includes('/family') || 
        location.pathname.includes('/pantry') || 
        location.pathname.includes('/recommendations') || 
        location.pathname.includes('/recipes') || 
        location.pathname.includes('/meal-planning')) return 1;
    // Books section
    if (location.pathname.includes('/books')) return 2;
    // TV Shows section
    if (location.pathname.includes('/tv-shows')) return 3;
    // Movies section
    if (location.pathname.includes('/movies')) return 4;
    return 0; // dashboard
  };

  // Enhanced navigation with content sections
  const navigationSections = [
    {
      title: 'Main',
      items: [
        { label: 'Dashboard', icon: <HomeIcon />, path: '/dashboard' }
      ]
    },
    {
      title: 'Food & Recipes',
      icon: <FoodIcon />,
      items: [
        { label: 'Family', icon: <PeopleIcon />, path: '/family' },
        { label: 'Pantry', icon: <KitchenIcon />, path: '/pantry' },
        { label: 'Recommendations', icon: <RecommendationsIcon />, path: '/recommendations' },
        { label: 'Saved Recipes', icon: <SavedRecipesIcon />, path: '/recipes' },
        { label: 'Meal Plans', icon: <CalendarIcon />, path: '/meal-planning' }
      ]
    },
    {
      title: 'Books',
      icon: <BooksIcon />,
      items: [
        { label: 'My Books', icon: <BooksIcon />, path: '/books' },
        { label: 'Recommendations', icon: <RecommendationsIcon />, path: '/books/recommendations' }
      ]
    },
    {
      title: 'TV Shows',
      icon: <TVIcon />,
      items: [
        { label: 'My Shows', icon: <TVIcon />, path: '/tv-shows' }
      ]
    },
    {
      title: 'Movies',
      icon: <MovieIcon />,
      items: [
        { label: 'My Movies', icon: <MovieIcon />, path: '/movies' }
      ]
    },
    {
      title: 'Other',
      items: [
        { label: 'Help', icon: <HelpIcon />, path: '/user-guide' },
        { label: 'Changes', icon: <HistoryIcon />, path: '/changes' },
        ...(user?.is_admin ? [{ label: 'Admin', icon: <AdminIcon />, path: '/admin' }] : [])
      ]
    }
  ];

  // Flatten for desktop tabs (backward compatibility)
  const navigationItems = navigationSections.flatMap(section => section.items);

  // Primary navigation for mobile bottom nav (main content sections)
  const primaryNavItems = [
    { label: 'Home', icon: <HomeIcon />, path: '/dashboard' },
    { label: 'Food', icon: <FoodIcon />, path: '/recipes' }, // Default to recipes as main food page
    { label: 'Books', icon: <BooksIcon />, path: '/books' },
    { label: 'TV Shows', icon: <TVIcon />, path: '/tv-shows' },
    { label: 'Movies', icon: <MovieIcon />, path: '/movies' }
  ];

  // Secondary items for drawer (non-primary content)
  const secondaryNavItems = navigationSections.find(section => section.title === 'Other')?.items || [];

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

  const toggleSection = (sectionTitle: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionTitle]: !prev[sectionTitle]
    }));
  };

  const handleDeleteAccount = async () => {
    if (confirmationText.toLowerCase() !== 'delete my account') {
      setSnackbarMessage('Please type "delete my account" to confirm');
      setSnackbarOpen(true);
      return;
    }

    setDeleteLoading(true);
    try {
      await apiRequest('DELETE', '/auth/delete-account');
      setSnackbarMessage('Account deleted successfully. Goodbye!');
      setSnackbarOpen(true);
      
      // Wait a moment to show the message, then logout
      setTimeout(() => {
        logout();
        navigate('/login');
      }, 2000);
      
    } catch (error: any) {
      console.error('Error deleting account:', error);
      setSnackbarMessage(error.response?.data?.detail || 'Failed to delete account');
      setSnackbarOpen(true);
    } finally {
      setDeleteLoading(false);
      setDeleteDialogOpen(false);
      setConfirmationText('');
    }
  };

  const openDeleteDialog = () => {
    setDeleteDialogOpen(true);
    setMobileDrawerOpen(false);
  };

  // Mobile Drawer Component
  const mobileDrawer = (
    <Box sx={{ width: 280 }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" color="primary.main" fontWeight="bold">
          📱 Content Hub
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
      
      {/* Hierarchical Navigation Sections */}
      {navigationSections.map((section, sectionIndex) => (
        <React.Fragment key={section.title}>
          {section.title !== 'Main' && (
            <>
              {sectionIndex > 1 && <Divider sx={{ my: 1 }} />}
              
              {/* Section Header */}
              {section.items.length > 1 ? (
                <ListItemButton
                  onClick={() => toggleSection(section.title)}
                  sx={{ 
                    py: 1,
                    backgroundColor: 'grey.50',
                    '&:hover': {
                      backgroundColor: 'grey.100'
                    }
                  }}
                >
                  <ListItemIcon sx={{ color: 'primary.main' }}>
                    {section.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={section.title}
                    primaryTypographyProps={{
                      fontWeight: 'medium',
                      fontSize: '0.875rem',
                      color: 'primary.main'
                    }}
                  />
                  {expandedSections[section.title] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </ListItemButton>
              ) : (
                <ListItem sx={{ py: 0.5, backgroundColor: 'grey.50' }}>
                  <ListItemIcon sx={{ color: 'primary.main' }}>
                    {section.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={section.title}
                    primaryTypographyProps={{
                      fontWeight: 'medium',
                      fontSize: '0.875rem',
                      color: 'primary.main'
                    }}
                  />
                </ListItem>
              )}
            </>
          )}
          
          {/* Section Items */}
          {(section.title === 'Main' || section.items.length === 1 || expandedSections[section.title]) && (
            <List sx={{ pl: section.title === 'Main' ? 0 : 2 }}>
              {section.items.map((item) => {
                const isSelected = location.pathname === item.path ||
                  (item.path === '/recipes' && getCurrentBottomNav() === 1) ||
                  (item.path === '/books' && getCurrentBottomNav() === 2) ||
                  (item.path === '/tv-shows' && getCurrentBottomNav() === 3) ||
                  (item.path === '/movies' && getCurrentBottomNav() === 4);
                
                return (
                  <ListItemButton 
                    key={item.path}
                    onClick={() => handleDrawerNavigation(item.path)}
                    selected={isSelected}
                    sx={{ 
                      py: 1.5,
                      pl: section.title === 'Main' ? 2 : 1
                    }}
                  >
                    <ListItemIcon sx={{ 
                      color: isSelected ? 'primary.main' : 'inherit',
                      minWidth: 36
                    }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={item.label} 
                      primaryTypographyProps={{ 
                        fontWeight: isSelected ? 'medium' : 'normal',
                        fontSize: section.title === 'Main' ? '1rem' : '0.875rem'
                      }}
                    />
                  </ListItemButton>
                );
              })}
            </List>
          )}
        </React.Fragment>
      ))}
      
      <Divider sx={{ my: 1 }} />
      
      {/* Theme Toggle */}
      <List>
        <ListItem sx={{ px: 2, py: 1 }}>
          <ThemeToggle variant="icon" showLabel />
        </ListItem>
      </List>
      
      <Divider sx={{ my: 1 }} />
      
      {/* Account Actions */}
      <List>
        <ListItemButton onClick={logout} sx={{ py: 1.5, color: 'warning.main' }}>
          <ListItemIcon sx={{ color: 'warning.main' }}>
            <CloseIcon />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItemButton>
        
        <ListItemButton 
          onClick={openDeleteDialog} 
          sx={{ 
            py: 1.5, 
            color: 'error.main',
            '&:hover': {
              backgroundColor: 'error.light',
              color: 'error.contrastText',
            }
          }}
        >
          <ListItemIcon sx={{ color: 'inherit' }}>
            <DeleteIcon />
          </ListItemIcon>
          <ListItemText primary="Delete Account" />
        </ListItemButton>
      </List>
    </Box>
  );

  // Desktop Sidebar Component
  const desktopSidebar = (
    <Box sx={{ 
      width: 280, 
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      borderRight: '1px solid',
      borderColor: 'divider',
      bgcolor: 'background.paper',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      overflowX: 'hidden',
    }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h5" color="primary.main" fontWeight="bold" gutterBottom>
          📱 Content Hub
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Welcome, {user?.name || user?.email}
        </Typography>
      </Box>
      
      {/* Navigation Sections */}
      <Box sx={{ flex: 1, py: 2 }}>
        {navigationSections.map((section, sectionIndex) => (
          <Box key={section.title} sx={{ mb: sectionIndex < navigationSections.length - 1 ? 1 : 0 }}>
            {section.title !== 'Main' && (
              <>
                {/* Section Header */}
                {section.items.length > 1 ? (
                  <ListItemButton
                    onClick={() => toggleSection(section.title)}
                    sx={{ 
                      px: 3,
                      py: 1.5,
                      '&:hover': {
                        backgroundColor: 'action.hover'
                      }
                    }}
                  >
                    <ListItemIcon sx={{ color: 'primary.main', minWidth: 40 }}>
                      {section.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={section.title}
                      primaryTypographyProps={{
                        fontWeight: 'medium',
                        fontSize: '0.95rem',
                      }}
                    />
                    {expandedSections[section.title] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </ListItemButton>
                ) : (
                  <Box sx={{ px: 3, py: 1.5 }}>
                    <Typography variant="subtitle2" color="text.secondary" fontWeight="medium">
                      {section.title}
                    </Typography>
                  </Box>
                )}
              </>
            )}
            
            {/* Section Items */}
            <Collapse in={section.title === 'Main' || section.items.length === 1 || expandedSections[section.title]} timeout="auto" unmountOnExit>
              <List sx={{ py: 0 }}>
                {section.items.map((item) => {
                  const isSelected = location.pathname === item.path;
                  
                  return (
                    <ListItemButton 
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      selected={isSelected}
                      sx={{ 
                        px: section.title === 'Main' ? 3 : 5,
                        py: 1.25,
                        '&.Mui-selected': {
                          backgroundColor: 'action.selected',
                          borderRight: '3px solid',
                          borderColor: 'primary.main',
                          '&:hover': {
                            backgroundColor: 'action.selected',
                          }
                        }
                      }}
                    >
                      <ListItemIcon sx={{ 
                        color: isSelected ? 'primary.main' : 'text.secondary',
                        minWidth: 40
                      }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText 
                        primary={item.label} 
                        primaryTypographyProps={{ 
                          fontWeight: isSelected ? 'medium' : 'normal',
                          fontSize: '0.875rem'
                        }}
                      />
                    </ListItemButton>
                  );
                })}
              </List>
            </Collapse>
            
            {sectionIndex < navigationSections.length - 1 && (
              <Divider sx={{ mx: 3, my: 1 }} />
            )}
          </Box>
        ))}
      </Box>
      
      {/* Bottom Actions */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ mb: 2 }}>
          <ThemeToggle variant="icon" showLabel fullWidth />
        </Box>
        
        <Button 
          fullWidth
          onClick={logout}
          variant="outlined"
          color="inherit"
          sx={{ mb: 1 }}
        >
          Logout
        </Button>
        
        <Button 
          fullWidth
          onClick={openDeleteDialog}
          variant="text"
          color="error"
          size="small"
          startIcon={<DeleteIcon />}
        >
          Delete Account
        </Button>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ 
      display: 'flex',
      minHeight: '100vh',
      bgcolor: 'background.default'
    }}>
      {/* Desktop Sidebar - always visible on desktop */}
      {!isMobile && desktopSidebar}
      
      {/* Main Content Area */}
      <Box sx={{ 
        flexGrow: 1,
        ml: !isMobile ? '280px' : 0, // Push content right on desktop
        pb: isMobile ? 7 : 0, // Add bottom padding for mobile bottom nav
        display: 'flex',
        flexDirection: 'column',
        width: '100%'
      }}>
        {/* Mobile Header */}
        {isMobile && (
          <AppBar position="sticky" elevation={0}>
            <Toolbar sx={{ minHeight: 56 }}>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
              
              <Typography 
                variant="h6" 
                component="div" 
                sx={{ 
                  flexGrow: 1,
                  fontWeight: 'bold',
                  fontSize: '1.1rem'
                }}
              >
                📱 Content Hub
              </Typography>
            </Toolbar>
          </AppBar>
        )}

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

      {/* Delete Account Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            ...(isMobile && {
              margin: 2,
              width: 'calc(100% - 32px)',
            }),
          },
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2,
          color: 'error.main',
          pb: 1
        }}>
          <WarningIcon />
          <Typography variant="h6" component="span" fontWeight="bold">
            Delete Account
          </Typography>
        </DialogTitle>
        
        <DialogContent>
          <DialogContentText sx={{ mb: 3 }}>
            <strong>⚠️ This action cannot be undone!</strong>
          </DialogContentText>
          
          <DialogContentText sx={{ mb: 3 }}>
            Deleting your account will permanently remove:
          </DialogContentText>
          
          <Box component="ul" sx={{ pl: 2, mb: 3 }}>
            <Typography component="li" variant="body2" color="text.secondary">
              Your profile and personal information
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              All family members and their dietary preferences
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Your entire pantry inventory
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              All meal plans and recommendations
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Meal reviews and ratings
            </Typography>
          </Box>
          
          <Alert severity="error" sx={{ mb: 3 }}>
            <strong>Warning:</strong> This will permanently delete all your data. 
            This action cannot be reversed.
          </Alert>
          
          <DialogContentText sx={{ mb: 2, fontWeight: 'medium' }}>
            To confirm, please type <strong>"delete my account"</strong> below:
          </DialogContentText>
          
          <TextField
            fullWidth
            value={confirmationText}
            onChange={(e) => setConfirmationText(e.target.value)}
            placeholder="delete my account"
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                '&.Mui-focused fieldset': {
                  borderColor: 'error.main',
                },
              },
            }}
          />
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={() => {
              setDeleteDialogOpen(false);
              setConfirmationText('');
            }}
            variant="outlined"
            size={isMobile ? "large" : "medium"}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAccount}
            variant="contained"
            color="error"
            disabled={deleteLoading || confirmationText.toLowerCase() !== 'delete my account'}
            size={isMobile ? "large" : "medium"}
            startIcon={deleteLoading ? undefined : <DeleteIcon />}
            sx={{ minWidth: 140 }}
          >
            {deleteLoading ? 'Deleting...' : 'Delete Account'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        sx={{ mb: isMobile ? 8 : 0 }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarMessage.includes('successfully') ? 'success' : 'error'}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Layout;