import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Alert,
} from '@mui/material';
import { Add, Edit, Delete, Person } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FamilyMember, FamilyMemberCreate } from '../../types';
import { apiRequest } from '../../services/api';

const familyMemberSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.union([z.number().min(0).max(120), z.literal('')]).optional(),
});

type FamilyMemberFormData = z.infer<typeof familyMemberSchema>;

const FamilyManagement: React.FC = () => {
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FamilyMemberFormData>({
    resolver: zodResolver(familyMemberSchema),
  });

  const fetchFamilyMembers = async () => {
    try {
      setLoading(true);
      const members = await apiRequest<FamilyMember[]>('GET', '/family/members');
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
    fetchFamilyMembers();
  }, []);

  const handleAddMember = () => {
    setEditingMember(null);
    reset({ name: '', age: '' });
    setIsDialogOpen(true);
  };

  const handleEditMember = (member: FamilyMember) => {
    setEditingMember(member);
    reset({ 
      name: member.name, 
      age: member.age || '' 
    });
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
        age: data.age === '' ? undefined : Number(data.age),
        dietary_restrictions: [],
        preferences: {
          likes: [],
          dislikes: [],
          preferred_cuisines: [],
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
      setError(editingMember ? 'Failed to update family member' : 'Failed to add family member');
      console.error('Error saving family member:', error);
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
            <Grid key={member.id} size={{ xs: 12, sm: 6, md: 4 }}>
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
                          <Chip key={index} label={restriction} size="small" />
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
              {...register('age', { valueAsNumber: true })}
              error={!!errors.age}
              helperText={errors.age?.message}
            />
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