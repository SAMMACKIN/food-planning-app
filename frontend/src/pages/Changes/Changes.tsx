import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  NewReleases,
  BugReport,
  AutoAwesome,
  Security,
  Speed,
  Add,
  Build,
  DataObject,
  Restaurant,
  CalendarToday,
  People,
  Kitchen,
  FilterList,
  MenuBook,
  Star,
  Refresh,
} from '@mui/icons-material';

interface ChangeEntry {
  version: string;
  date: string;
  type: 'major' | 'minor' | 'patch';
  changes: {
    type: 'feature' | 'improvement' | 'bugfix' | 'security';
    description: string;
    icon: React.ReactNode;
  }[];
}

const changeHistory: ChangeEntry[] = [
  {
    version: "1.5.0",
    date: "June 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Recipe Cards Redesign - Compact 4x3 grid layout showing 12 recipes per page",
        icon: <Restaurant />
      },
      {
        type: "feature",
        description: "Advanced Recipe Filtering - Filter by difficulty, preparation time, and meal type",
        icon: <FilterList />
      },
      {
        type: "feature",
        description: "Enhanced Cooking Instructions - Step-by-step visual guide with numbered circles and connecting lines",
        icon: <MenuBook />
      },
      {
        type: "feature",
        description: "User Recipe Creation - Create and save your own custom recipes with full ingredient and instruction management",
        icon: <Add />
      },
      {
        type: "feature",
        description: "Smart AI Learning - AI now learns from your recipe ratings to suggest better personalized recommendations",
        icon: <Star />
      },
      {
        type: "feature",
        description: "Recipe Similarity Prevention - AI avoids suggesting recipes too similar to recently saved or poorly rated ones",
        icon: <Refresh />
      },
      {
        type: "improvement",
        description: "Enhanced Recipe Saving Debug Tools - Comprehensive troubleshooting capabilities with detailed error logging",
        icon: <BugReport />
      },
      {
        type: "improvement",
        description: "Better Error Handling - Improved error messages and user feedback throughout the recipe system",
        icon: <AutoAwesome />
      },
      {
        type: "improvement",
        description: "Reusable Recipe Components - Created modular components for better code maintainability",
        icon: <Build />
      }
    ]
  },
  {
    version: "1.4.0",
    date: "June 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Admin Dashboard with user management and system statistics",
        icon: <Security />
      },
      {
        type: "feature",
        description: "Multi-provider AI support - Added Groq alongside Claude AI",
        icon: <AutoAwesome />
      },
      {
        type: "improvement", 
        description: "Environment-specific database separation (preview vs production)",
        icon: <DataObject />
      },
      {
        type: "improvement",
        description: "Automated test data population for preview environment",
        icon: <Build />
      },
      {
        type: "bugfix",
        description: "Fixed Groq model compatibility - using llama-3.1-8b-instant",
        icon: <BugReport />
      },
      {
        type: "feature",
        description: "Meal plan persistence - Save AI recommendations directly to meal plans",
        icon: <CalendarToday />
      },
      {
        type: "feature",
        description: "Meal review system - Rate and review tried meals with 5-star ratings",
        icon: <Restaurant />
      },
      {
        type: "improvement",
        description: "Increased AI recommendations from 5 to 10 per request",
        icon: <AutoAwesome />
      },
      {
        type: "security",
        description: "Secure API key management via environment variables only",
        icon: <Security />
      }
    ]
  },
  {
    version: "1.3.0",
    date: "June 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Enhanced pantry management with multi-select ingredient adding",
        icon: <Kitchen />
      },
      {
        type: "improvement",
        description: "Real-time ingredient search with category grouping and nutritional info",
        icon: <Speed />
      },
      {
        type: "improvement",
        description: "Visual checkboxes and improved UX for ingredient selection",
        icon: <AutoAwesome />
      },
      {
        type: "security",
        description: "Database persistence fixes for Railway deployments with persistent volumes",
        icon: <DataObject />
      }
    ]
  },
  {
    version: "1.2.0",
    date: "May 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Weekly meal planning calendar with 7-day view",
        icon: <CalendarToday />
      },
      {
        type: "feature",
        description: "Meal assignment system with AI recommendations integration",
        icon: <Restaurant />
      },
      {
        type: "improvement",
        description: "Responsive meal planning grid that works on all devices",
        icon: <Speed />
      },
      {
        type: "improvement",
        description: "Week navigation with previous/next controls",
        icon: <AutoAwesome />
      }
    ]
  },
  {
    version: "1.1.0",
    date: "April 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Family member management with comprehensive food preferences",
        icon: <People />
      },
      {
        type: "feature",
        description: "Dietary restrictions support (Vegetarian, Vegan, Gluten-Free, etc.)",
        icon: <Security />
      },
      {
        type: "feature",
        description: "Cuisine preferences and food likes/dislikes tracking",
        icon: <Restaurant />
      },
      {
        type: "improvement",
        description: "Enhanced Claude AI integration using family preferences for personalized recommendations",
        icon: <AutoAwesome />
      }
    ]
  },
  {
    version: "1.0.0",
    date: "March 2025",
    type: "major",
    changes: [
      {
        type: "feature",
        description: "Initial release with user authentication system",
        icon: <Security />
      },
      {
        type: "feature",
        description: "Basic pantry management with ingredient tracking",
        icon: <Kitchen />
      },
      {
        type: "feature",
        description: "Claude AI-powered meal recommendations",
        icon: <AutoAwesome />
      },
      {
        type: "feature",
        description: "Responsive React frontend with Material-UI design",
        icon: <Build />
      },
      {
        type: "feature",
        description: "FastAPI backend with SQLite database",
        icon: <DataObject />
      },
      {
        type: "feature",
        description: "Cloud deployment on Railway and Vercel",
        icon: <Speed />
      }
    ]
  }
];

const upcomingFeatures = [
  {
    title: "Shopping List Generation",
    description: "Automatically generate shopping lists based on meal plans and pantry inventory",
    priority: "High",
    status: "Planned"
  },
  {
    title: "Recipe Import",
    description: "Import recipes from URLs or manual entry with automatic ingredient parsing",
    priority: "Medium",
    status: "Planned"
  },
  {
    title: "Nutrition Tracking",
    description: "Detailed nutritional analysis for meals and daily intake tracking",
    priority: "Medium",
    status: "Planned"
  },
  {
    title: "Push Notifications",
    description: "Meal reminders, expiring ingredient alerts, and meal planning notifications",
    priority: "Medium",
    status: "Planned"
  },
  {
    title: "Mobile App",
    description: "Native mobile applications for iOS and Android",
    priority: "Low",
    status: "Considering"
  }
];

const getChangeTypeIcon = (type: string) => {
  switch (type) {
    case 'feature': return <Add color="success" />;
    case 'improvement': return <AutoAwesome color="primary" />;
    case 'bugfix': return <BugReport color="warning" />;
    case 'security': return <Security color="error" />;
    default: return <NewReleases />;
  }
};

const getChangeTypeColor = (type: string) => {
  switch (type) {
    case 'feature': return 'success';
    case 'improvement': return 'primary';
    case 'bugfix': return 'warning';
    case 'security': return 'error';
    default: return 'default';
  }
};

const getVersionTypeColor = (type: string) => {
  switch (type) {
    case 'major': return 'error';
    case 'minor': return 'warning';
    case 'patch': return 'success';
    default: return 'default';
  }
};

const Changes: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" component="h1" gutterBottom>
        Changes & Updates
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        Track all updates, new features, and improvements to the Food Planning App.
      </Typography>

      {/* Current Version */}
      <Card sx={{ mb: 4, bgcolor: 'primary.50', border: '2px solid', borderColor: 'primary.main' }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <NewReleases color="primary" sx={{ mr: 2 }} />
            <Typography variant="h5">
              Current Version: {changeHistory[0].version}
            </Typography>
            <Chip 
              label={changeHistory[0].type.toUpperCase()} 
              color={getVersionTypeColor(changeHistory[0].type) as any}
              size="small" 
              sx={{ ml: 2 }} 
            />
          </Box>
          <Typography variant="body1" color="text.secondary">
            Released: {changeHistory[0].date}
          </Typography>
        </CardContent>
      </Card>

      {/* Version History */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Version History
      </Typography>
      
      <Box>
        {changeHistory.map((entry, index) => (
          <Card key={entry.version} sx={{ mb: 3, border: '2px solid', borderColor: `${getVersionTypeColor(entry.type)}.main` }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <NewReleases sx={{ mr: 2, color: `${getVersionTypeColor(entry.type)}.main` }} />
                <Typography variant="h6">
                  Version {entry.version}
                </Typography>
                <Chip 
                  label={entry.type.toUpperCase()} 
                  color={getVersionTypeColor(entry.type) as any}
                  size="small" 
                  sx={{ ml: 2 }} 
                />
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                {entry.date}
              </Typography>
              
              <List dense>
                {entry.changes.map((change, changeIndex) => (
                  <ListItem key={changeIndex} disablePadding>
                    <ListItemIcon>
                      {getChangeTypeIcon(change.type)}
                    </ListItemIcon>
                    <ListItemText 
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2">
                            {change.description}
                          </Typography>
                          <Chip 
                            label={change.type} 
                            color={getChangeTypeColor(change.type) as any}
                            size="small" 
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={change.icon}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Upcoming Features */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            <Build sx={{ mr: 1, verticalAlign: 'middle' }} />
            Upcoming Features
          </Typography>
          <Typography variant="body1" color="text.secondary" mb={3}>
            Features currently in development or planned for future releases.
          </Typography>
          <Divider sx={{ mb: 3 }} />
          
          {upcomingFeatures.map((feature, index) => (
            <Card key={index} variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                  <Typography variant="h6">
                    {feature.title}
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Chip 
                      label={feature.priority} 
                      color={
                        feature.priority === 'High' ? 'error' : 
                        feature.priority === 'Medium' ? 'warning' : 'success'
                      }
                      size="small" 
                    />
                    <Chip 
                      label={feature.status} 
                      color="primary"
                      variant="outlined"
                      size="small" 
                    />
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </CardContent>
      </Card>

      {/* Feedback Section */}
      <Card sx={{ mt: 4, bgcolor: 'info.50' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            💡 Have Suggestions?
          </Typography>
          <Typography variant="body1">
            We're always looking to improve! If you have feature requests, bug reports, or general feedback, 
            please let us know. Your input helps shape the future of the Food Planning App.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Changes;