import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
} from '@mui/material';
import {
  ExpandMore,
  Dashboard,
  People,
  Kitchen,
  CalendarToday,
  Restaurant,
  PlayArrow,
  Lightbulb,
  Security,
} from '@mui/icons-material';

const UserGuide: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" component="h1" gutterBottom>
        User Guide
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        Complete guide to using the Food Planning App for meal planning, pantry management, and family preferences.
      </Typography>

      {/* Quick Start */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            <PlayArrow sx={{ mr: 1, verticalAlign: 'middle' }} />
            Quick Start
          </Typography>
          <Typography variant="body1" mb={2}>
            New to the app? Follow these steps to get started:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="1. Add Family Members" 
                secondary="Go to Family tab and add each family member with their dietary preferences"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="2. Stock Your Pantry" 
                secondary="Use the Pantry tab to add ingredients you currently have at home"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="3. Get Recommendations" 
                secondary="Visit Recommendations tab for AI-powered meal suggestions based on your preferences"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="4. Plan Your Week" 
                secondary="Use Meal Plans tab to organize your weekly meals"
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Feature Guides */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Feature Guides
      </Typography>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Dashboard sx={{ mr: 2 }} />
          <Typography variant="h6">Dashboard Overview</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography paragraph>
            Your dashboard provides a quick overview of your food planning activities:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Recent Activity" 
                secondary="See your latest pantry additions and meal plans"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Quick Stats" 
                secondary="View family members count, pantry items, and upcoming meals"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Expiring Items" 
                secondary="Get alerts for ingredients nearing expiration"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <People sx={{ mr: 2 }} />
          <Typography variant="h6">Family Management</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography paragraph>
            Manage your family members and their food preferences for personalized recommendations:
          </Typography>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Adding Family Members:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Basic Info" 
                secondary="Add name and age for each family member"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Dietary Restrictions" 
                secondary="Select from common restrictions: Vegetarian, Vegan, Gluten-Free, etc."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Food Preferences" 
                secondary="Add liked foods, disliked foods, and preferred cuisines"
              />
            </ListItem>
          </List>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Supported Dietary Restrictions:</Typography>
            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Nut-Free', 'Halal', 'Kosher', 'Keto'].map(diet => (
                <Chip key={diet} label={diet} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Kitchen sx={{ mr: 2 }} />
          <Typography variant="h6">Pantry Management</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography paragraph>
            Track your ingredients and manage your pantry inventory effectively:
          </Typography>
          <Typography variant="subtitle2" gutterBottom>
            Adding Ingredients:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Multi-Select" 
                secondary="Select multiple ingredients at once when adding to pantry"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Search & Filter" 
                secondary="Type to search ingredients by name, grouped by category"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Quantity & Expiration" 
                secondary="Set quantities and optional expiration dates"
              />
            </ListItem>
          </List>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Features:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Expiration Tracking" 
                secondary="Color-coded expiration dates (red=expired, yellow=soon, green=fresh)"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Category Organization" 
                secondary="Ingredients grouped by category (Meat, Dairy, Vegetables, etc.)"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Nutritional Info" 
                secondary="View calories and nutritional details for each ingredient"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <CalendarToday sx={{ mr: 2 }} />
          <Typography variant="h6">Meal Planning</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography paragraph>
            Plan your weekly meals with our intuitive calendar interface:
          </Typography>
          <Typography variant="subtitle2" gutterBottom>
            How to Plan Meals:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Weekly View" 
                secondary="See all 7 days of the week with 4 meal types each"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Add Meals" 
                secondary="Click any empty meal slot to browse and select from recommendations"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Week Navigation" 
                secondary="Use Previous/Next Week buttons to plan ahead"
              />
            </ListItem>
          </List>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Meal Types:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map(meal => (
              <Chip key={meal} label={meal} color="primary" size="small" />
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Restaurant sx={{ mr: 2 }} />
          <Typography variant="h6">AI Recommendations</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography paragraph>
            Get personalized meal recommendations powered by Claude AI:
          </Typography>
          <Typography variant="subtitle2" gutterBottom>
            How Recommendations Work:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Family Preferences" 
                secondary="AI considers each family member's dietary restrictions and preferences"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Pantry Optimization" 
                secondary="Suggestions prioritize ingredients you already have"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Variety & Balance" 
                secondary="AI ensures nutritional balance and meal variety"
              />
            </ListItem>
          </List>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Recommendation Details:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Prep Time & Difficulty" 
                secondary="Each recipe shows cooking time and skill level required"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Ingredients List" 
                secondary="Complete ingredient list with quantities"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Lightbulb /></ListItemIcon>
              <ListItemText 
                primary="Step-by-Step Instructions" 
                secondary="Detailed cooking instructions for each recipe"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      {/* Tips & Best Practices */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            <Lightbulb sx={{ mr: 1, verticalAlign: 'middle' }} />
            Tips & Best Practices
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="h6" gutterBottom>Pantry Management Tips:</Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Regular Updates" 
                secondary="Update pantry quantities after shopping and cooking"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Expiration Monitoring" 
                secondary="Check the dashboard regularly for items nearing expiration"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Bulk Adding" 
                secondary="Use multi-select feature when adding multiple ingredients from shopping trips"
              />
            </ListItem>
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Meal Planning Tips:</Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Plan Ahead" 
                secondary="Plan meals 1-2 weeks in advance for better organization"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Balance Variety" 
                secondary="Mix different cuisines and cooking methods throughout the week"
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Consider Schedule" 
                secondary="Plan quick meals for busy days, elaborate ones for weekends"
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
            Data & Privacy
          </Typography>
          <Typography variant="body1" paragraph>
            Your data privacy and security are important to us:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><Security /></ListItemIcon>
              <ListItemText 
                primary="Secure Authentication" 
                secondary="Your account is protected with secure password hashing and JWT tokens"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Security /></ListItemIcon>
              <ListItemText 
                primary="Private Data" 
                secondary="Your family and pantry data is private to your account only"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Security /></ListItemIcon>
              <ListItemText 
                primary="AI Processing" 
                secondary="Meal recommendations are generated securely without storing personal preferences externally"
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default UserGuide;