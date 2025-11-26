import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  Folder as FolderIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  Login as LoginIcon,
  FiberManualRecord as ActiveIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { adminAPI, api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { useImpersonation } from '../../contexts/ImpersonationContext';

interface User {
  id: number;
  email: string;
  full_name?: string;
  organization?: string;
  tenant_id?: number;
  is_admin: boolean;
  is_active: boolean;
  is_invited: boolean;
  invitation_expires_at?: string;
  created_at: string;
}

interface Tenant {
  id: number;
  tenant_name: string;
  primary_color: string;
  secondary_color: string;
}

interface ActiveUser {
  id: number;
  email: string;
  full_name: string | null;
  last_activity: string | null;
  activity_type: string | null;
}

interface ActiveUsersData {
  count: number;
  active_users: ActiveUser[];
  minutes_threshold: number;
  current_admin_id: number;
}

const UserManagement: React.FC = () => {
  const { isAdmin } = useAuth();
  const { setImpersonatedUser } = useImpersonation();
  const navigate = useNavigate();

  const [users, setUsers] = useState<User[]>([]);
  const [activeUsers, setActiveUsers] = useState<ActiveUsersData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Tenants
  const [tenants, setTenants] = useState<Tenant[]>([]);

  // Invite dialog
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteFullName, setInviteFullName] = useState('');
  const [inviteOrganization, setInviteOrganization] = useState('');
  const [inviteTenantId, setInviteTenantId] = useState<number | ''>('');


  // Edit dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editIsActive, setEditIsActive] = useState(false);
  const [editIsAdmin, setEditIsAdmin] = useState(false);

  // Menu state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuUser, setMenuUser] = useState<User | null>(null);

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);



  useEffect(() => {
    if (isAdmin) {
      loadUsers();
      loadTenants();
      loadActiveUsers();
    }

    // Auto-refresh active users every 60 seconds
    const interval = setInterval(() => {
      if (isAdmin) {
        loadActiveUsers();
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [isAdmin]);

  const loadTenants = async () => {
    try {
      const data = await adminAPI.listTenants();
      setTenants(data);
    } catch (err: any) {
      console.error('Failed to load tenants:', err);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.listUsers();
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadActiveUsers = async () => {
    try {
      const response = await api.get('/admin/active-users?minutes=15');
      setActiveUsers(response.data);
    } catch (err: any) {
      console.error('Failed to load active users:', err);
    }
  };

  const isUserActive = (userId: number) => {
    return activeUsers?.active_users.some(u => u.id === userId) || false;
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleString();
  };

  const handleInviteUser = async () => {
    setError('');
    setSuccess('');

    if (!inviteEmail || !inviteFullName) {
      setError('Email and full name are required');
      return;
    }

    try {
      const tenantIdToUse = inviteTenantId === '' ? undefined : inviteTenantId;
      const response = await adminAPI.createInvitation(inviteEmail, inviteFullName, inviteOrganization, tenantIdToUse);

      // Close the invite dialog
      setInviteDialogOpen(false);

      // Reset form
      setInviteEmail('');
      setInviteFullName('');
      setInviteOrganization('');
      setInviteTenantId('');

      // Reload users to get the new user
      await loadUsers();

      // Find the newly created user by email and send invitation email
      const users = await adminAPI.listUsers();
      const newUser = users.find((u: User) => u.email === inviteEmail);

      if (newUser) {
        try {
          await adminAPI.sendInvitationEmail(newUser.id);
          setSuccess(`User ${inviteEmail} added and invitation email sent!`);
        } catch (emailErr: any) {
          console.error('Failed to send invitation email:', emailErr);
          setSuccess(`User ${inviteEmail} added successfully`);
          setError('Note: Invitation email failed to send. You can resend from the table.');
        }
      } else {
        setSuccess(`User ${inviteEmail} added successfully`);
      }

    } catch (err: any) {
      console.error('Failed to create invitation:', err);
      setError(err.response?.data?.detail || 'Failed to create invitation');
    }
  };


  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setEditIsActive(user.is_active);
    setEditIsAdmin(user.is_admin);
    setEditDialogOpen(true);
  };

  const handleSaveUserChanges = async () => {
    if (!editingUser) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.updateUserStatus(editingUser.id, {
        is_active: editIsActive,
        is_admin: editIsAdmin,
      });

      setSuccess(`User ${editingUser.email} updated successfully`);
      setEditDialogOpen(false);
      setEditingUser(null);
      loadUsers();
    } catch (err: any) {
      console.error('Failed to update user:', err);
      setError(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLButtonElement>, user: User) => {
    setMenuAnchorEl(event.currentTarget);
    setMenuUser(user);
  };

  const handleCloseMenu = () => {
    setMenuAnchorEl(null);
    setMenuUser(null);
  };

  const handleViewBrands = async () => {
    if (!menuUser) return;

    try {
      // Get user's brands
      const brands = await adminAPI.getUserBrands(menuUser.id);

      if (brands.length === 0) {
        setError(`User ${menuUser.email} has no brands yet`);
        handleCloseMenu();
        return;
      }

      // Navigate to the first brand (or could show a selection dialog if multiple)
      navigate(`/admin/users/${menuUser.id}/brands/${brands[0].id}`);
      handleCloseMenu();
    } catch (err: any) {
      console.error('Failed to load user brands:', err);
      setError('Failed to load user brands');
      handleCloseMenu();
    }
  };

  const handleDeleteUser = () => {
    if (!menuUser) return;
    setUserToDelete(menuUser);
    setDeleteDialogOpen(true);
    handleCloseMenu();
  };

  const handleConfirmDelete = async () => {
    if (!userToDelete) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.deleteUser(userToDelete.id);
      setSuccess(`User ${userToDelete.email} deleted successfully`);
      setDeleteDialogOpen(false);
      setUserToDelete(null);
      // Refresh user list
      loadUsers();
    } catch (err: any) {
      console.error('Failed to delete user:', err);
      setError(err.response?.data?.detail || 'Failed to delete user');
      setDeleteDialogOpen(false);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setUserToDelete(null);
  };

  const handleSendInvitation = async (user: User) => {
    console.log('handleSendInvitation called for user:', user);
    setError('');
    setSuccess('');

    try {
      console.log('Calling sendInvitationEmail API...');
      const result = await adminAPI.sendInvitationEmail(user.id);
      console.log('API response:', result);
      setSuccess(`Invitation email sent to ${user.email}!`);
    } catch (err: any) {
      console.error('Failed to send invitation email:', err);
      setError(err.response?.data?.detail || 'Failed to send invitation email');
    }
  };

  const handleLoginAsUser = async () => {
    if (!menuUser) return;

    if (!window.confirm(`Log in as ${menuUser.email}? This will open a new tab where you'll be logged in as this user.`)) {
      handleCloseMenu();
      return;
    }

    try {
      const response = await api.post(`/admin/login-as-user/${menuUser.id}`);
      const { access_token } = response.data;

      // Fetch user data with the new token
      const userResponse = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      const userData = userResponse.data;

      // Store the impersonation data in sessionStorage (not localStorage) on the parent tab
      // This way it won't interfere with your admin session
      const impersonationData = {
        token: access_token,
        user: userData,
        timestamp: Date.now()
      };

      // Use sessionStorage with a unique key
      sessionStorage.setItem('tales_impersonation', JSON.stringify(impersonationData));

      // Open new tab and pass the impersonation key
      const newTab = window.open(`${window.location.origin}/?impersonate=${Date.now()}`, '_blank');

      if (!newTab) {
        setError('Please allow popups to use the "Login As" feature');
      }

      handleCloseMenu();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate login token');
      handleCloseMenu();
    }
  };

  const handleViewAsUser = () => {
    if (!menuUser) return;

    // Set the impersonated user in context
    setImpersonatedUser({
      id: menuUser.id,
      email: menuUser.email,
      full_name: menuUser.full_name,
    });

    handleCloseMenu();

    // Navigate to dashboard
    navigate('/');
  };


  const columns: GridColDef[] = [
    {
      field: 'email',
      headerName: 'Email',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => {
        const user = params.row as User;
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isUserActive(user.id) && (
              <ActiveIcon sx={{ fontSize: 12, color: 'success.main' }} />
            )}
            {user.email}
          </Box>
        );
      },
    },
    {
      field: 'full_name',
      headerName: 'Full Name',
      flex: 0.8,
      minWidth: 150,
    },
    {
      field: 'tenant_id',
      headerName: 'Tenant',
      flex: 0.8,
      minWidth: 150,
      renderCell: (params) => {
        const user = params.row as User;
        const tenant = tenants.find(t => t.id === user.tenant_id);
        return tenant ? tenant.tenant_name : '-';
      },
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const user = params.row as User;
        if (!user.is_active && user.is_invited) {
          return <Chip label="Pending" color="warning" size="small" />;
        }
        return (
          <Chip
            label={user.is_active ? 'Active' : 'Inactive'}
            color={user.is_active ? 'success' : 'default'}
            size="small"
          />
        );
      },
    },
    {
      field: 'is_admin',
      headerName: 'Admin',
      width: 100,
      renderCell: (params) =>
        params.value ? <Chip label="Admin" color="primary" size="small" /> : null,
    },
    {
      field: 'invitation',
      headerName: 'Invitation',
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Button
          size="small"
          variant="outlined"
          startIcon={<EmailIcon />}
          onClick={() => handleSendInvitation(params.row as User)}
        >
          Send
        </Button>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton onClick={() => handleEditUser(params.row as User)} size="small" color="primary">
            <EditIcon />
          </IconButton>
          <IconButton onClick={(e) => handleOpenMenu(e, params.row as User)} size="small">
            <MoreVertIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  if (!isAdmin) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
        <Alert severity="error">You do not have permission to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setInviteDialogOpen(true)}
        >
          Invite User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Active Users Alert */}
      {activeUsers && activeUsers.count > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }} icon={<ActiveIcon />}>
          <Typography variant="body1" fontWeight="bold">
            {activeUsers.count} user{activeUsers.count !== 1 ? 's' : ''} currently active (last {activeUsers.minutes_threshold} minutes)
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Consider waiting before deploying if users are actively working.
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            {activeUsers.active_users.map((user) => (
              <li key={user.id}>
                <Typography variant="caption">
                  {user.email} - {user.activity_type} ({formatDateTime(user.last_activity)})
                </Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}

      {activeUsers && activeUsers.count === 0 && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="body1" fontWeight="bold">
            No other users currently active - Safe to deploy
          </Typography>
        </Alert>
      )}

      <Paper elevation={2}>
        <DataGrid
          rows={users}
          columns={columns}
          loading={loading}
          autoHeight
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 10 } },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite New User</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Add a user's email address to the approved list. They can sign in with Google, Microsoft, or create a password.
          </Typography>

          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            required
            sx={{ mb: 2, mt: 1 }}
          />

          <TextField
            fullWidth
            label="Full Name"
            value={inviteFullName}
            onChange={(e) => setInviteFullName(e.target.value)}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Organization"
            value={inviteOrganization}
            onChange={(e) => setInviteOrganization(e.target.value)}
            sx={{ mb: 2 }}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="tenant-select-label">Tenant (Optional)</InputLabel>
            <Select
              labelId="tenant-select-label"
              id="tenant-select"
              value={inviteTenantId}
              label="Tenant (Optional)"
              onChange={(e) => setInviteTenantId(e.target.value as number | '')}
            >
              <MenuItem value="">
                <em>Use My Tenant (Default)</em>
              </MenuItem>
              {tenants.map((tenant) => (
                <MenuItem key={tenant.id} value={tenant.id}>
                  {tenant.tenant_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="caption" color="text.secondary">
            Leave tenant as default to assign user to your tenant. Select a specific tenant to assign them to a different organization.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleInviteUser} variant="contained" disabled={!inviteEmail}>
            Add User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User: {editingUser?.email}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={editIsActive}
                  onChange={(e) => setEditIsActive(e.target.checked)}
                />
              }
              label="Active"
            />
            <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Inactive users cannot log in
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={editIsAdmin}
                  onChange={(e) => setEditIsAdmin(e.target.checked)}
                />
              }
              label="Admin"
            />
            <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4 }}>
              Admins can manage users and view all data
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveUserChanges} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Actions Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={handleViewAsUser}>
          <ListItemIcon>
            <VisibilityIcon fontSize="small" color="primary" />
          </ListItemIcon>
          <ListItemText>View As User</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLoginAsUser}>
          <ListItemIcon>
            <LoginIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Login As User</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleViewBrands}>
          <ListItemIcon>
            <FolderIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Brands</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDeleteUser}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete User</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCancelDelete}>
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user <strong>{userToDelete?.email}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will permanently delete the user and all their associated brands and data. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;
