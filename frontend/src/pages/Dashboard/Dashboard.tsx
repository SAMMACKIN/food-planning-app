import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  useTheme,
  useMediaQuery,
  Stack,
  Avatar,
  Divider,
} from '@mui/material';
import {
  FamilyRestroom,
  Kitchen,
  CalendarMonth,
  Restaurant,
  Add as AddIcon,
  ShoppingCart as ShoppingCartIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const dashboardCards = [
    {
      title: 'Family',
      description: 'Manage family members and dietary preferences',
      icon: FamilyRestroom,
      action: () => navigate('/family'),
      actionLabel: 'Manage Family',
      color: theme.palette.success.main,
      gradient: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.light} 100%)`,
    },
    {
      title: 'Pantry',
      description: 'Track ingredients and inventory',
      icon: Kitchen,
      action: () => navigate('/pantry'),
      actionLabel: 'View Pantry',
      color: theme.palette.warning.main,
      gradient: `linear-gradient(135deg, ${theme.palette.warning.main} 0%, ${theme.palette.warning.light} 100%)`,
    },
    {
      title: 'Meal Plans',
      description: 'Plan weekly meals and schedules',
      icon: CalendarMonth,
      action: () => navigate('/meal-planning'),
      actionLabel: 'Plan Meals',
      color: theme.palette.info.main,
      gradient: `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.light} 100%)`,
    },
    {
      title: 'Recipes',
      description: 'AI-powered meal suggestions',
      icon: Restaurant,
      action: () => navigate('/recommendations'),
      actionLabel: 'Get Recipes',
      color: theme.palette.primary.main,
      gradient: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.light} 100%)`,
    },
  ];

  const quickActions = [
    {
      label: 'Add Family Member',
      icon: AddIcon,
      action: () => navigate('/family'),
      variant: 'contained' as const,
      color: 'primary' as const,
    },
    {
      label: 'Update Pantry',
      icon: TrendingUpIcon,
      action: () => navigate('/pantry'),
      variant: 'contained' as const,
      color: 'secondary' as const,
    },
    {
      label: 'Shopping List',
      icon: ShoppingCartIcon,
      action: () => console.log('Generate shopping list'),
      variant: 'outlined' as const,
      color: 'primary' as const,
    },
  ];

  return (
    <Box sx={{ pb: 2 }}>
      {/* Header */}
      <Box sx={{ mb: isMobile ? 2 : 3 }}>
        <Typography 
          variant={isMobile ? "h2" : "h1"} 
          component="h1" 
          sx={{ 
            fontWeight: 700,
            background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.light} 100%)`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1
          }}
        >
          {isMobile ? '🏠 Dashboard' : '🏠 Food Planning Dashboard'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Let's plan some delicious meals.
        </Typography>
      </Box>

      {/* Main Cards */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { 
          xs: '1fr', 
          sm: '1fr 1fr', 
          md: '1fr 1fr', 
          lg: '1fr 1fr 1fr 1fr' 
        }, 
        gap: isMobile ? 2 : 3, 
        mb: 4 
      }}>
        {dashboardCards.map((card, index) => (
          <Card 
            key={card.title}
            sx={{ 
              height: '100%',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              background: isMobile 
                ? `linear-gradient(135deg, ${card.color}08 0%, ${card.color}04 100%)`
                : 'transparent', // Use theme background instead of hardcoded white
              border: isMobile ? `1px solid ${card.color}20` : 'none',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: `0 8px 25px ${card.color}25`,
              },
            }}
            onClick={card.action}
          >
              <CardContent sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                height: '100%',
                position: 'relative',
                overflow: 'hidden'
              }}>
                {/* Decorative gradient overlay for mobile */}
                {isMobile && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      right: 0,
                      width: 80,
                      height: 80,
                      background: card.gradient,
                      borderRadius: '50%',
                      opacity: 0.1,
                      transform: 'translate(25px, -25px)',
                    }}
                  />
                )}
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, zIndex: 1 }}>
                  <Avatar
                    sx={{
                      bgcolor: card.color,
                      background: card.gradient,
                      mr: 2,
                      width: isMobile ? 48 : 40,
                      height: isMobile ? 48 : 40,
                    }}
                  >
                    <card.icon />
                  </Avatar>
                  <Typography 
                    variant={isMobile ? "h3" : "h4"} 
                    component="h2"
                    sx={{ fontWeight: 600 }}
                  >
                    {card.title}
                  </Typography>
                </Box>
                
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ 
                    mb: 3, 
                    flexGrow: 1,
                    lineHeight: 1.5,
                    fontSize: isMobile ? '0.875rem' : '0.8rem'
                  }}
                >
                  {card.description}
                </Typography>
                
                <Button 
                  variant={isMobile ? "contained" : "outlined"}
                  size={isMobile ? "medium" : "small"}
                  onClick={(e) => {
                    e.stopPropagation();
                    card.action();
                  }}
                  sx={{
                    alignSelf: 'flex-start',
                    ...(isMobile && {
                      background: card.gradient,
                      border: 'none',
                      color: 'white',
                      '&:hover': {
                        background: card.gradient,
                        opacity: 0.9,
                      },
                    }),
                  }}
                >
                  {card.actionLabel}
                </Button>
              </CardContent>
            </Card>
        ))}
      </Box>

      <Divider sx={{ my: 3 }} />

      {/* Quick Actions */}
      <Box>
        <Typography 
          variant={isMobile ? "h3" : "h2"} 
          component="h2" 
          sx={{ mb: 3, fontWeight: 600 }}
        >
          🚀 Quick Actions
        </Typography>
        
        {isMobile ? (
          <Stack spacing={2}>
            {quickActions.map((action) => (
              <Button
                key={action.label}
                variant={action.variant}
                color={action.color}
                size="large"
                startIcon={<action.icon />}
                onClick={action.action}
                fullWidth
                sx={{
                  py: 2,
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                }}
              >
                {action.label}
              </Button>
            ))}
          </Stack>
        ) : (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {quickActions.map((action) => (
              <Button
                key={action.label}
                variant={action.variant}
                color={action.color}
                startIcon={<action.icon />}
                onClick={action.action}
              >
                {action.label}
              </Button>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default Dashboard;