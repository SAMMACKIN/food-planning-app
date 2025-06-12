import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
} from '@mui/material';
import {
  FamilyRestroom,
  Kitchen,
  CalendarMonth,
  Restaurant,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <FamilyRestroom color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Family</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Manage family members and their dietary preferences
              </Typography>
              <Button variant="outlined" size="small" onClick={() => navigate('/family')}>
                Manage Family
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Kitchen color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Pantry</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Track ingredients and manage your pantry inventory
              </Typography>
              <Button variant="outlined" size="small" onClick={() => navigate('/pantry')}>
                View Pantry
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CalendarMonth color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Meal Plans</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Plan your weekly meals and track attendance
              </Typography>
              <Button variant="outlined" size="small">
                Plan Meals
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Restaurant color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Recommendations</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Get AI-powered meal suggestions based on your preferences
              </Typography>
              <Button variant="outlined" size="small" onClick={() => navigate('/recommendations')}>
                Get Suggestions
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box mt={4}>
        <Typography variant="h5" component="h2" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid size="auto">
            <Button variant="contained" color="primary" onClick={() => navigate('/family')}>
              Add Family Member
            </Button>
          </Grid>
          <Grid size="auto">
            <Button variant="contained" color="secondary" onClick={() => navigate('/pantry')}>
              Update Pantry
            </Button>
          </Grid>
          <Grid size="auto">
            <Button variant="outlined">
              Generate Shopping List
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default Dashboard;