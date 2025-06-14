import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Tabs,
  Tab,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  AdminPanelSettings,
  People,
  Groups,
  TrendingUp,
  PersonAdd,
  DataUsage,
  Security,
  Group,
  Restaurant,
} from '@mui/icons-material';
import { apiRequest } from '../../services/api';

interface User {
  id: string;
  email: string;
  name?: string;
  timezone: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface FamilyMember {
  id: string;
  user_id: string;
  name: string;
  age?: number;
  dietary_restrictions: string[];
  preferences: any;
  created_at: string;
  user_email: string;
  user_name?: string;
}

interface AdminStats {
  total_users: number;
  total_family_members: number;
  total_pantry_items: number;
  recent_registrations: number;
}

const AdminDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const [usersData, familyData, statsData] = await Promise.all([
        apiRequest<User[]>('GET', '/admin/users'),
        apiRequest<FamilyMember[]>('GET', '/admin/family/all'),
        apiRequest<AdminStats>('GET', '/admin/stats')
      ]);
      
      setUsers(usersData);
      setFamilyMembers(familyData);
      setStats(statsData);
      setError(null);
    } catch (error: any) {
      setError('Failed to fetch admin data');
      console.error('Error fetching admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase();
    }
    return email ? email[0].toUpperCase() : '?';
  };

  if (loading) {
    return (
      <Box p={3}>
        <Typography variant="h4" gutterBottom>Admin Dashboard</Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={3}>
        <AdminPanelSettings sx={{ mr: 2, fontSize: 32, color: 'error.main' }} />
        <Typography variant="h4" component="h1">
          Admin Dashboard
        </Typography>
      </Box>
      
      <Typography variant="body1" color="text.secondary" mb={4}>
        System overview and user management for the Food Planning App.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Overview */}
      {stats && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
          <Box>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <People sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" component="div">
                  {stats.total_users}
                </Typography>
                <Typography color="text.secondary">
                  Total Users
                </Typography>
              </CardContent>
            </Card>
          </Box>
          
          <Box>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Groups sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" component="div">
                  {stats.total_family_members}
                </Typography>
                <Typography color="text.secondary">
                  Family Members
                </Typography>
              </CardContent>
            </Card>
          </Box>
          
          <Box>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Restaurant sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4" component="div">
                  {stats.total_pantry_items}
                </Typography>
                <Typography color="text.secondary">
                  Pantry Items
                </Typography>
              </CardContent>
            </Card>
          </Box>
          
          <Box>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <PersonAdd sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                <Typography variant="h4" component="div">
                  {stats.recent_registrations}
                </Typography>
                <Typography color="text.secondary">
                  New Users (30d)
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Data Tables */}
      <Card>
        <CardContent>
          <Tabs value={currentTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab 
              label={`Users (${users.length})`}
              icon={<People />}
              iconPosition="start"
            />
            <Tab 
              label={`Family Members (${familyMembers.length})`}
              icon={<Group />}
              iconPosition="start"
            />
          </Tabs>

          {/* Users Tab */}
          {currentTab === 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                All Users
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Registered</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Avatar sx={{ mr: 2, bgcolor: user.is_admin ? 'error.main' : 'primary.main' }}>
                              {getInitials(user.name, user.email)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {user.name || 'No name'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                ID: {user.id.substring(0, 8)}...
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Chip 
                            label={user.is_admin ? 'Admin' : 'User'} 
                            color={user.is_admin ? 'error' : 'primary'}
                            size="small"
                            icon={user.is_admin ? <Security /> : <People />}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={user.is_active ? 'Active' : 'Inactive'} 
                            color={user.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(user.created_at)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Family Members Tab */}
          {currentTab === 1 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                All Family Members
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Family Member</TableCell>
                      <TableCell>User Account</TableCell>
                      <TableCell>Age</TableCell>
                      <TableCell>Dietary Restrictions</TableCell>
                      <TableCell>Added</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {familyMembers.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Avatar sx={{ mr: 2, bgcolor: 'success.main' }}>
                              {getInitials(member.name)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {member.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                ID: {member.id.substring(0, 8)}...
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2">
                              {member.user_email}
                            </Typography>
                            {member.user_name && (
                              <Typography variant="caption" color="text.secondary">
                                {member.user_name}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {member.age ? `${member.age} years` : 'Not specified'}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" flexWrap="wrap" gap={0.5}>
                            {member.dietary_restrictions.length > 0 ? (
                              member.dietary_restrictions.map((restriction, index) => (
                                <Chip 
                                  key={index} 
                                  label={restriction} 
                                  size="small" 
                                  variant="outlined"
                                  color="warning"
                                />
                              ))
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(member.created_at)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Admin Warning */}
      <Alert severity="warning" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          🔒 Admin Access
        </Typography>
        You are viewing sensitive user data. Please ensure this information is handled according to privacy policies and data protection regulations.
      </Alert>
    </Box>
  );
};

export default AdminDashboard;