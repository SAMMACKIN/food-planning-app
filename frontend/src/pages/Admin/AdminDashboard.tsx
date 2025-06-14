import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
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
  LinearProgress,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Snackbar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  AdminPanelSettings,
  People,
  Groups,
  PersonAdd,
  Security,
  Group,
  Restaurant,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Lock as LockIcon,
  Warning as WarningIcon,
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
  
  // User management states
  const [userMenuAnchor, setUserMenuAnchor] = useState<{ [key: string]: HTMLElement | null }>({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

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

  // User management functions
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>, userId: string) => {
    setUserMenuAnchor({ ...userMenuAnchor, [userId]: event.currentTarget });
  };

  const handleUserMenuClose = (userId: string) => {
    setUserMenuAnchor({ ...userMenuAnchor, [userId]: null });
  };

  const openDeleteDialog = (user: User) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
    handleUserMenuClose(user.id);
  };

  const openResetPasswordDialog = (user: User) => {
    setSelectedUser(user);
    setResetPasswordDialogOpen(true);
    setNewPassword('');
    setConfirmPassword('');
    handleUserMenuClose(user.id);
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    setActionLoading(true);
    try {
      await apiRequest('DELETE', `/admin/users/${selectedUser.id}`);
      setSnackbarMessage(`User ${selectedUser.email} deleted successfully`);
      setSnackbarOpen(true);
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      fetchAdminData(); // Refresh data
    } catch (error: any) {
      setSnackbarMessage(error.response?.data?.detail || 'Failed to delete user');
      setSnackbarOpen(true);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUser || !newPassword || newPassword !== confirmPassword) {
      setSnackbarMessage('Please ensure passwords match and are not empty');
      setSnackbarOpen(true);
      return;
    }

    setActionLoading(true);
    try {
      await apiRequest('POST', `/admin/users/${selectedUser.id}/reset-password`, {
        new_password: newPassword
      });
      setSnackbarMessage(`Password reset successfully for ${selectedUser.email}`);
      setSnackbarOpen(true);
      setResetPasswordDialogOpen(false);
      setSelectedUser(null);
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      setSnackbarMessage(error.response?.data?.detail || 'Failed to reset password');
      setSnackbarOpen(true);
    } finally {
      setActionLoading(false);
    }
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
                      <TableCell align="right">Actions</TableCell>
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
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={(event) => handleUserMenuOpen(event, user.id)}
                            disabled={user.is_admin}
                          >
                            <MoreVertIcon />
                          </IconButton>
                          <Menu
                            anchorEl={userMenuAnchor[user.id]}
                            open={Boolean(userMenuAnchor[user.id])}
                            onClose={() => handleUserMenuClose(user.id)}
                          >
                            <MenuItem onClick={() => openResetPasswordDialog(user)}>
                              <ListItemIcon>
                                <LockIcon fontSize="small" />
                              </ListItemIcon>
                              <ListItemText>Reset Password</ListItemText>
                            </MenuItem>
                            <MenuItem onClick={() => openDeleteDialog(user)} sx={{ color: 'error.main' }}>
                              <ListItemIcon>
                                <DeleteIcon fontSize="small" color="error" />
                              </ListItemIcon>
                              <ListItemText>Delete User</ListItemText>
                            </MenuItem>
                          </Menu>
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

      {/* Delete User Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 2, color: 'error.main' }}>
          <WarningIcon />
          <Typography variant="h6" component="span" fontWeight="bold">
            Delete User Account
          </Typography>
        </DialogTitle>
        
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            <strong>⚠️ This action cannot be undone!</strong>
          </DialogContentText>
          
          {selectedUser && (
            <DialogContentText sx={{ mb: 3 }}>
              Are you sure you want to permanently delete the account for <strong>{selectedUser.email}</strong>?
            </DialogContentText>
          )}
          
          <DialogContentText sx={{ mb: 2 }}>
            This will permanently remove:
          </DialogContentText>
          
          <Box component="ul" sx={{ pl: 2, mb: 2 }}>
            <Typography component="li" variant="body2" color="text.secondary">
              User profile and personal information
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              All family members and dietary preferences
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Pantry inventory and meal plans
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Reviews and user-generated content
            </Typography>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteUser}
            variant="contained"
            color="error"
            disabled={actionLoading}
            startIcon={<DeleteIcon />}
          >
            {actionLoading ? 'Deleting...' : 'Delete User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog
        open={resetPasswordDialogOpen}
        onClose={() => setResetPasswordDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <LockIcon />
          <Typography variant="h6" component="span" fontWeight="bold">
            Reset User Password
          </Typography>
        </DialogTitle>
        
        <DialogContent>
          {selectedUser && (
            <DialogContentText sx={{ mb: 3 }}>
              Reset password for <strong>{selectedUser.email}</strong>
            </DialogContentText>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Confirm Password"
            type="password"
            fullWidth
            variant="outlined"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmPassword !== '' && newPassword !== confirmPassword}
            helperText={confirmPassword !== '' && newPassword !== confirmPassword ? 'Passwords do not match' : ''}
          />
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={() => setResetPasswordDialogOpen(false)}
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleResetPassword}
            variant="contained"
            disabled={actionLoading || !newPassword || newPassword !== confirmPassword}
            startIcon={<LockIcon />}
          >
            {actionLoading ? 'Resetting...' : 'Reset Password'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
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

export default AdminDashboard;