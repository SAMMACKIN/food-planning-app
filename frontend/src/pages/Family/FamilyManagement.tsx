import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemText,
} from '@mui/material';
import { Grid2 as Grid } from '@mui/material';
import { Add, Edit, Delete, Person } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FamilyMember, FamilyMemberCreate } from '../../types';
import { apiRequest } from '../../services/api';

const familyMemberSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.coerce.number().min(0, 'Age must be 0 or greater').max(120, 'Age must be 120 or less').optional().or(z.literal('')),
  dietary_restrictions: z.array(z.string()).optional(),
  food_likes: z.string().optional(),
  food_dislikes: z.string().optional(),
  preferred_cuisines: z.array(z.string()).optional(),
});

type FamilyMemberFormData = z.infer<typeof familyMemberSchema>;

const DIETARY_RESTRICTIONS = [
  'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Nut-Free', 
  'Soy-Free', 'Egg-Free', 'Halal', 'Kosher', 'Low-Carb', 'Keto'
];

const CUISINE_TYPES = [
  'Italian', 'Chinese', 'Mexican', 'Indian', 'Thai', 'Japanese', 
  'Mediterranean', 'American', 'French', 'Korean', 'Vietnamese', 'Greek'
];

const FamilyManagement: React.FC = () => {
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDietaryRestrictions, setSelectedDietaryRestrictions] = useState<string[]>([]);
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FamilyMemberFormData>({
    resolver: zodResolver(familyMemberSchema),
  });

  const fetchFamilyMembers = async () => {
    console.log('👨‍👩‍👧‍👦 fetchFamilyMembers called - starting fetch...');
    try {
      setLoading(true);
      const members = await apiRequest<FamilyMember[]>('GET', '/family/members', null, { requestType: 'navigation' });
      setFamilyMembers(members);
      setError(null);
    } catch (error: any) {
      setError('Failed to fetch family members');
      console.error('Error fetching family members:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('👨‍👩‍👧‍👦 FamilyManagement mounted - fetching data...');
    fetchFamilyMembers();
  }, []);

  const handleAddMember = () => {
    setEditingMember(null);
    reset({ name: '', age: undefined, food_likes: '', food_dislikes: '' });
    setSelectedDietaryRestrictions([]);
    setSelectedCuisines([]);
    setIsDialogOpen(true);
  };

  const handleEditMember = (member: FamilyMember) => {
    setEditingMember(member);
    reset({ 
      name: member.name, 
      age: member.age,
      food_likes: member.preferences?.likes?.join(', ') || '',
      food_dislikes: member.preferences?.dislikes?.join(', ') || ''
    });
    setSelectedDietaryRestrictions(member.dietary_restrictions || []);
    setSelectedCuisines(member.preferences?.preferred_cuisines || []);
    setIsDialogOpen(true);
  };

  const handleDeleteMember = async (memberId: string) => {
    if (!window.confirm('Are you sure you want to delete this family member?')) {
      return;
    }

    try {
      await apiRequest('DELETE', `/family/members/${memberId}`);
      await fetchFamilyMembers();
    } catch (error: any) {
      setError('Failed to delete family member');
      console.error('Error deleting family member:', error);
    }
  };

  const onSubmit = async (data: FamilyMemberFormData) => {
    try {
      setLoading(true);
      const memberData: FamilyMemberCreate = {
        name: data.name,
        age: data.age === '' || data.age === undefined ? undefined : Number(data.age),
        dietary_restrictions: selectedDietaryRestrictions,
        preferences: {
          likes: data.food_likes ? data.food_likes.split(',').map(s => s.trim()) : [],
          dislikes: data.food_dislikes ? data.food_dislikes.split(',').map(s => s.trim()) : [],
          preferred_cuisines: selectedCuisines,
          spice_level: 0
        }
      };

      if (editingMember) {
        await apiRequest('PUT', `/family/members/${editingMember.id}`, memberData);
      } else {
        await apiRequest('POST', '/family/members', memberData);
      }

      await fetchFamilyMembers();
      setIsDialogOpen(false);
      reset();
      setError(null);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`${editingMember ? 'Failed to update' : 'Failed to add'} family member: ${errorMessage}`);
      console.error('Error saving family member:', error);
      console.error('Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Family Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleAddMember}
          disabled={loading}
        >
          Add Family Member
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {familyMembers.length === 0 && !loading ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Person sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No family members yet
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Add family members to start planning meals for everyone
            </Typography>
            <Button variant="contained" startIcon={<Add />} onClick={handleAddMember}>
              Add Your First Family Member
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {familyMembers.map((member) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={member.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" component="h2">
                      {member.name}
                    </Typography>
                    <Box>
                      <IconButton 
                        size="small" 
                        onClick={() => handleEditMember(member)}
                        disabled={loading}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        onClick={() => handleDeleteMember(member.id)}
                        disabled={loading}
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </Box>
                  
                  {member.age && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Age: {member.age}
                    </Typography>
                  )}
                  
                  {member.dietary_restrictions.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" gutterBottom>
                        Dietary Restrictions:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {member.dietary_restrictions.map((restriction, index) => (
                          <Chip key={index} label={restriction} size="small" color="secondary" />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {member.preferences?.preferred_cuisines && member.preferences.preferred_cuisines.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" gutterBottom>
                        Preferred Cuisines:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {member.preferences.preferred_cuisines.map((cuisine, index) => (
                          <Chip key={index} label={cuisine} size="small" color="primary" />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {member.preferences?.likes && member.preferences.likes.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" gutterBottom>
                        Likes:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {member.preferences.likes.map((food, index) => (
                          <Chip key={index} label={food} size="small" variant="outlined" color="success" />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {member.preferences?.dislikes && member.preferences.dislikes.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" gutterBottom>
                        Dislikes:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {member.preferences.dislikes.map((food, index) => (
                          <Chip key={index} label={food} size="small" variant="outlined" color="error" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>
            {editingMember ? 'Edit Family Member' : 'Add Family Member'}
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Name"
              fullWidth
              variant="outlined"
              {...register('name')}
              error={!!errors.name}
              helperText={errors.name?.message}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Age (optional)"
              type="number"
              fullWidth
              variant="outlined"
              {...register('age')}
              error={!!errors.age}
              helperText={errors.age?.message}
              sx={{ mb: 2 }}
              inputProps={{
                min: 0,
                max: 120,
                step: 1
              }}
            />
            
            <TextField
              margin="dense"
              label="Food Likes (comma separated)"
              fullWidth
              variant="outlined"
              placeholder="e.g. pizza, chicken, broccoli"
              {...register('food_likes')}
              sx={{ mb: 2 }}
            />
            
            <TextField
              margin="dense"
              label="Food Dislikes (comma separated)"
              fullWidth
              variant="outlined"
              placeholder="e.g. mushrooms, spicy food, fish"
              {...register('food_dislikes')}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Dietary Restrictions</InputLabel>
              <Select
                multiple
                value={selectedDietaryRestrictions}
                onChange={(e) => setSelectedDietaryRestrictions(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                input={<OutlinedInput label="Dietary Restrictions" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {DIETARY_RESTRICTIONS.map((restriction) => (
                  <MenuItem key={restriction} value={restriction}>
                    <Checkbox checked={selectedDietaryRestrictions.indexOf(restriction) > -1} />
                    <ListItemText primary={restriction} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Preferred Cuisines</InputLabel>
              <Select
                multiple
                value={selectedCuisines}
                onChange={(e) => setSelectedCuisines(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                input={<OutlinedInput label="Preferred Cuisines" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {CUISINE_TYPES.map((cuisine) => (
                  <MenuItem key={cuisine} value={cuisine}>
                    <Checkbox checked={selectedCuisines.indexOf(cuisine) > -1} />
                    <ListItemText primary={cuisine} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setIsDialogOpen(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? 'Saving...' : editingMember ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default FamilyManagement;